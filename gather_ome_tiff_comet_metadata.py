"""
Scan COMET folder for .ome.tiff or .ome.ome.tiff files, extract metadata from each image using tifffile
(including bit depth, dimensions, samples per pixel, pyramid levels, level dimensions, physical sizes,
channels, and objective magnification), and save the collected information to an Excel file. Records
any errors encountered while processing files.
"""

import os
import tifffile
import pandas as pd
import xml.etree.ElementTree as ET

folder_path = r"/mnt/nas-data/jblab/group_folders/emily_lythgoe/COMET/DAPI"
data = []

for filename in os.listdir(folder_path):
    if filename.lower().endswith(".ome.tiff") or filename.lower().endswith(".ome.ome.tiff"):
        filepath = os.path.join(folder_path, filename)
        try:
            with tifffile.TiffFile(filepath) as tif:
                series = tif.series[0]
                dtype = series.dtype
                bit_depth = dtype.itemsize * 8 if dtype else None
                size_y, size_x = series.levels[0].shape[-2:]
                samples_per_pixel = series.shape[-1] if series.ndim >= 3 else 1

                # Extract level dimensions
                level_dimensions = []
                for i, level in enumerate(series.levels):
                    h, w = level.shape[-2:]
                    level_dimensions.append(f"Level {i}: {w}x{h}")
                level_str = "; ".join(level_dimensions)

                # Parse OME-XML metadata
                ome_xml = tif.ome_metadata
                objective_power = None
                physical_size_x = None
                physical_size_y = None
                channels = None

                if ome_xml:
                    root = ET.fromstring(ome_xml)
                    ns = {'ome': 'http://www.openmicroscopy.org/Schemas/OME/2016-06'}
                    pixels = root.find('.//ome:Pixels', ns)
                    if pixels is not None:
                        physical_size_x = pixels.attrib.get('PhysicalSizeX')
                        physical_size_y = pixels.attrib.get('PhysicalSizeY')
                        channels = [ch.attrib.get('Name', '') for ch in pixels.findall('ome:Channel', ns)]

                    instrument = root.find('.//ome:Instrument', ns)
                    if instrument is not None:
                        objective = instrument.find('.//ome:Objective', ns)
                        if objective is not None:
                            objective_power = objective.attrib.get('NominalMagnification')

                data.append({
                    "Filename": filename,
                    "BitDepth": bit_depth,
                    "SizeX": size_x,
                    "SizeY": size_y,
                    "SamplesPerPixel": samples_per_pixel,
                    "Levels": len(series.levels),
                    "LevelDimensions": level_str,
                    "PhysicalSizeX (μm)": physical_size_x,
                    "PhysicalSizeY (μm)": physical_size_y,
                    "Channels": ", ".join(channels) if channels else None,
                    "ObjectivePower": objective_power
                })

        except Exception as e:
            data.append({
                "Filename": filename,
                "Error": str(e)
            })

# Save to Excel
df = pd.DataFrame(data)
output_path = os.path.join(folder_path, "COMET_metadata.xlsx")
df.to_excel(output_path, index=False)
print(f"Metadata saved to {output_path}")



