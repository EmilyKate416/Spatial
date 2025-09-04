"""
Scan Visium H&E for .svs whole-slide images, extract metadata (level count, dimensions, downsampling, base size, MPP, objective power) using OpenSlide, and save the results to an Excel file. Records errors for any slides that cannot be opened.
"""

import openslide
import os
import pandas as pd


folder_path = r"/mnt/nas-data/fmlab/group_folders/lythgo02/Spatial/Visium_H&E"

data = []

for filename in os.listdir(folder_path):
    if filename.lower().endswith('.svs'):
        filepath = os.path.join(folder_path, filename)
        try:
            slide = openslide.OpenSlide(filepath)
            data.append({
                "Filename": filename,
                "Level count": slide.level_count,
                "Level dimensions": slide.level_dimensions,
                "Level downsamples": slide.level_downsamples,
                "Base level size": slide.level_dimensions[0],
                "MPP_x": slide.properties.get('openslide.mpp-x'),
                "MPP_y": slide.properties.get('openslide.mpp-y'),
                "Objective power": slide.properties.get('openslide.objective-power'),
            })
        except Exception as e:
            data.append({
                "Filename": filename,
                "Error": str(e)
            })

df = pd.DataFrame(data)
df.to_excel(r"/mnt/nas-data/fmlab/group_folders/lythgo02/Spatial/Visium_H&E/hne_slide_info.xlsx", index=False)
print("Slide info saved to slide_info.xlsx")

