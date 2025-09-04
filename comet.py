"""
Used in: submit_savetoVIPs.sh

Purpose
-------
Prep large microscopy datasets for COMET–H&E co-registration:
- Read COMET DAPI OME-TIFF pyramids lazily (tifffile → Zarr) and normalize.
- Read H&E whole-slide images (OpenSlide) and build a pseudo-DAPI channel.
- Handle per-sample resolution differences (20× vs 40×) with optional rescaling.
- Export pyramid BigTIFFs (pyvips) for downstream registration (e.g., VALIS).

Inputs
------
- Master metadata Excel (e.g., 20250513_valis_meta_scratch1.xlsx) with columns:
  • MedicalAchiever, COMET_DAPI_path, H&E_path
- COMET OME-TIFF DAPI files (multi-resolution pyramid)
- H&E whole-slide images (Aperio/SVS or compatible)

Outputs
-------
- For each sample (MedicalAchiever subfolder under save_ome):
  • pseudo-dapi-comet.tif      (8-bit, tiled pyramid BigTIFF)
  • pseudo-dapi-hne-40x.tif    (8-bit, tiled pyramid BigTIFF)
- Console logs of shapes, scaling decisions, and progress

Notes
-----
- Dependencies: numpy, pandas, tifffile, zarr, scikit-image, OpenSlide, pyvips, cv2, napari (optional).
- COMET is higher resolution than Ultivue; script normalizes/optionally rescales to harmonize.
- Memory-safe: reads OME-TIFF via Zarr; avoid full in-RAM loads for gigapixel images.
"""
# ------------------------------------------------------------------------------
# Environment Setup
# ------------------------------------------------------------------------------
# micromamba activate napari-env
# (may need to downgrade libffi)
# micromamba install libffi=3.3
# pip install napari[all]
#
# Added to ~/.bashrc (so no need to run manually each session):
#   export PATH="$HOME/local/libvips/bin:$PATH"
#   export PKG_CONFIG_PATH="$HOME/local/libvips/lib64/pkgconfig:$PKG_CONFIG_PATH"
#   export LD_LIBRARY_PATH="$HOME/local/libvips/lib64:/home/lythgo02/micromamba/pkgs/libffi-3.4.6-h2dba641_1/lib:/home/lythgo02/micromamba/envs/napari-env/lib:$LD_LIBRARY_PATH"
#
# ------------------------------------------------------------------------------
# Metadata Gathering (run once before registration)
# ------------------------------------------------------------------------------
# python "/mnt/fmlab/group_folders/lythgo02/Spatial/scripts/gather_ome_tiff_comet_metadata.py"
# python "/mnt/fmlab/group_folders/lythgo02/Spatial/scripts/gather_h&e_meta_data.py"
# python "/mnt/nas-data/fmlab/group_folders/lythgo02/Spatial/scripts/gather_ultivue_metadata.py"
#
# ------------------------------------------------------------------------------
# Imaging Summary
# ------------------------------------------------------------------------------
# COMET OME-TIFF:
# - File: '20230703_CRU00162406-041_DAPI.ome.ome.tiff' ~4 GiB
# - Shape: (39570, 39490), Axes: YX (2D, single channel)
# - Bit depth: uint16 (SignificantBits=16)
# - Resolution: ~0.23 µm/pixel (43.49 µm⁻¹)
# - Objective: 20× air, NA 0.75
#
# Ultivue:
# - Scanned at 20×
# - Resolution: 0.49773 µm/pixel
# - Bit depth: 8-bit
# - COMET is ~2× higher resolution → downsample COMET to match Ultivue
#
# H&E:
# - Scanned at 40×
# - Bit depth: 8-bit
# - Multi-level pyramids (levels 1,4,16,32 or 1,4,16)
# ------------------------------------------------------------------------------

# python
# Import packages
# Import packages
import os
import pandas as pd
import cv2
import numpy as np
from scipy.stats import scoreatpercentile
import skimage as ski
import napari
import tifffile as tff
import zarr
import gc
import openslide

import pyvips



# Define paths for batch processing
#rawpath = "/mnt/scratchc/fmlab/lythgo02/COMET/DAPI"
hne_path = "/mnt/scratchc/fmlab/lythgo02/Spatial/Visium_H&E/"
save_ome = "/mnt/scratchc/fmlab/lythgo02/Spatial/valis_prep_comet_hne40x/" #valis_prep_cometlayer3_hne40x/"

# Load master metadata sheet
master_df = pd.read_excel("/mnt/scratchc/fmlab/lythgo02/Spatial/20250513_valis_meta_scratch1.xlsx")
reg_df = master_df

# Visualisation flag
visualise = 0
if visualise:
    viewer = napari.Viewer()

region = (0, 0)
level = 0
dapi_idx = 0

ii=0

# Loop through datasets to co-register
for idx, row in reg_df.iterrows():
    file_id = row["MedicalAchiever"]
    print(f"Preparing data for co-registration: {file_id}")
    out_folder = os.path.join(save_ome, file_id)
    if os.path.exists(out_folder):
        print("FILE ALREADY EXPORTED")
        continue
    if not os.path.exists(row["COMET_DAPI_path"]):
        print("No valid DAPI path found — skipping.")
        continue
    dapi_path = row["COMET_DAPI_path"]
    tif = tff.TiffFile(dapi_path)
    position_series = tif.series[0] # Use Zarr to avoid loading into memory the complete image
    position_zarr = zarr.open(position_series.aszarr(), mode='r')
    position_zarr = position_zarr[0] #choose pyramid/resolution
    print(np.shape(position_zarr))
    if position_zarr.ndim == 3: # Load DAPI image and preprocess it
        wsiStain = np.array(position_zarr[int(dapi_idx), :, :])
    elif position_zarr.ndim == 2:
        wsiStain = np.array(position_zarr)
    else:
        raise ValueError(f"Unexpected array shape: {position_zarr.shape}")
    upcy5_wb = scoreatpercentile(wsiStain,99.95)
    lwcy5_wb = scoreatpercentile(wsiStain,0.05)
    wsiStain[wsiStain > upcy5_wb] = upcy5_wb
    wsiStain[wsiStain < lwcy5_wb] = lwcy5_wb        
    wsiStain[wsiStain<0]=0
    wsiStain = 255*(wsiStain-lwcy5_wb)/(upcy5_wb-lwcy5_wb)
    print(wsiStain.shape)
    downscale_ultivue = False  # set dynamically if needed # Downscale Ultivue DAPI by 0.925x
    if downscale_ultivue:
        print("Downscaling Ultivue DAPI by 0.9245x")
        wsiStain = ski.transform.rescale(wsiStain, 0.9245, anti_aliasing=True, preserve_range=True)
        print("Downscaled Ultivue DAPI shape:", wsiStain.shape)
    if not os.path.exists(row["H&E_path"]):
        print("No valid H&E path found — skipping.")
        continue
    hne_file_path = row["H&E_path"]
    wsi_hne = openslide.OpenSlide(hne_file_path)  # Load HnE image
    size = wsi_hne.level_dimensions[0]
    print(size)
    region_img = wsi_hne.read_region((0,0), level, size)
    rgba_array = np.array(region_img)
    red_channel = rgba_array[:, :, 0] # Split the RGBA channels
    green_channel = rgba_array[:, :, 1]
    blue_channel = rgba_array[:, :, 2]
    alpha_channel = rgba_array[:, :, 3]
    purple_intensity = 0.4975 * red_channel + 0.4975 * blue_channel + 0.005 * green_channel # Create a pseudo-DAPI from HnE as an inverted grayscale image using a weighted combination of red and blue channels
    purple_intensity = cv2.normalize(purple_intensity, None, 0, 255, cv2.NORM_MINMAX)
    purple_intensity = 255-purple_intensity    
    purple_intensity = np.where(alpha_channel>0, purple_intensity, 0).astype(np.uint8)
    if len(purple_intensity.shape) == 3 and purple_intensity.shape[2] == 1:
        purple_intensity = purple_intensity[:, :, 0]
    region_out = np.rot90(purple_intensity) # Aperio rotates 90degrees compared to COMET data
    shape_fixed = wsiStain.shape
    low_res_samples = ["CRU00162406-039", "CRU00167339-030"]  # scanned at 20x not 40x # Optional: Upscale H&E if scanned at lower resolution (e.g., 20x, ~0.5034 µm/pixel)
    if file_id in low_res_samples:
        region_out  = ski.transform.rescale(region_out,2.0)
    else:
        region_out  = ski.transform.rescale(region_out,1.0)   #set to 0.5 to downsacle the 40x to 20x
    print(f"No scaling applied for 40x H&E for {file_id}")
    shape_moving = region_out.shape
    print(shape_moving)
    cropped_region = 255*(region_out-np.min(region_out))/(np.max(region_out)-np.min(region_out)) # Output normalised pseudo-DAPI from HnE  
    if wsiStain.dtype != np.uint8:
        wsiStain = wsiStain.astype(np.uint8)
    if cropped_region.dtype != np.uint8:
        cropped_region = cropped_region.astype(np.uint8)   
    height, width = wsiStain.shape
    height_h, width_h = cropped_region.shape
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    # import pdb; pdb.set_trace()
    vips_image = pyvips.Image.new_from_memory(
        wsiStain.tobytes(), width, height, 1, 'uchar')
    vips_image.tiffsave(os.path.join(out_folder, "pseudo-dapi-comet.tif"), tile=True, pyramid=True, compression="none", bigtiff=True)
    vips_image2 = pyvips.Image.new_from_memory(
        cropped_region.tobytes(), width_h, height_h, 1, 'uchar')
    vips_image2.tiffsave(os.path.join(out_folder, "pseudo-dapi-hne-40x.tif"), tile=True, pyramid=True, compression="none", bigtiff=True)
    if visualise:
        viewer.add_image(cropped_region, name=f'Purple Intensity Image', blending='additive',opacity=1.0)
        viewer.add_image(wsiStain, name=f'Purple Intensity Image', blending='additive',opacity=1.0)
    wsi_hne.close()
    del red_channel, green_channel, blue_channel, rgba_array, cropped_region, wsiStain, tif, position_series, position_zarr, purple_intensity
    gc.collect()
    print('Saved DAPI/DAPI-like files')
    print('----')

