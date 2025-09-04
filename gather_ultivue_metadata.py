"""
Extract metadata from .tiff or OME-TIFF images listed in an Excel file.

The script reads an Excel file containing file paths (column 'Ultivue_DAPI_path'),
opens each image using tifffile, and extracts metadata including bit depth, 
image dimensions, samples per pixel, pyramid levels, level dimensions, physical 
sizes, channels, and objective magnification. Errors for any unreadable files 
are recorded. The collected metadata is saved to a new Excel file.
"""

import pandas as pd
import tifffile
import os
import xml.etree.ElementTree as ET

# Path to your meta Excel file with the Ultivue_DAPI_path column
meta_file = '/mnt/nas-data/fmlab/group_folders/lythgo02/visium_data/20250513_valis_meta.xlsx'

# Load the meta file
df_meta = pd.read_excel(meta_file)

# Prepare list to hold metadata dicts
metadata_list = []

def extract_tiff_metadata(filepath):
    try:
        with tifffile.TiffFile(filepath) as tif:
            num_levels = len(tif.pages)
            page0 = tif.pages[0]
            bit_depth = getattr(page0, 'bitspersample', None)
            size_x = getattr(page0, 'imagewidth', None)
            size_y = getattr(page0, 'imagelength', None)
            samples_per_pixel = getattr(page0, 'samplesperpixel', None)
            level_dims = [(p.imagewidth, p.imagelength) for p in tif.pages]

            physical_size_x = None
            physical_size_y = None
            channels = None
            objective_power = None

            ome_xml = tif.ome_metadata
            if ome_xml:
                root = ET.fromstring(ome_xml)
                ns = {'ome': 'http://www.openmicroscopy.org/Schemas/OME/2016-06'}
                pixels = root.find('.//ome:Pixels', ns)
                if pixels is not None:
                    physical_size_x = pixels.attrib.get('PhysicalSizeX', None)
                    physical_size_y = pixels.attrib.get('PhysicalSizeY', None)
                    channels = [ch.attrib.get('Name', '') for ch in pixels.findall('ome:Channel', ns)]
                instrument = root.find('.//ome:Instrument', ns)
                if instrument is not None:
                    objective = instrument.find('.//ome:Objective', ns)
                    if objective is not None:
                        objective_power = objective.attrib.get('NominalMagnification', None)

            return {
                "Filename": os.path.basename(filepath),
                "FullPath": filepath,
                "BitDepth": bit_depth,
                "SizeX_Level0": size_x,
                "SizeY_Level0": size_y,
                "SamplesPerPixel": samples_per_pixel,
                "NumberOfLevels": num_levels,
                "LevelDimensions": "; ".join([f"{w}x{h}" for w, h in level_dims]),
                "PhysicalSizeX": physical_size_x,
                "PhysicalSizeY": physical_size_y,
                "Channels": ", ".join(channels) if channels else None,
                "ObjectivePower": objective_power,
            }
    except Exception as e:
        return {
            "Filename": os.path.basename(filepath),
            "FullPath": filepath,
            "Error": str(e)
        }

# Iterate over the Ultivue_DAPI_path column
for idx, path in df_meta['Ultivue_DAPI_path'].dropna().items():
    metadata = extract_tiff_metadata(path)
    metadata_list.append(metadata)

# Create DataFrame with metadata
df_metadata = pd.DataFrame(metadata_list)

# Save to Excel
output_file = '/mnt/nas-data/fmlab/group_folders/lythgo02/visium_data/ultivue_dapi_metadata.xlsx'
df_metadata.to_excel(output_file, index=False)

print(f"Metadata extraction complete. Results saved to {output_file}")




