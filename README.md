
# Spatial QC and Registration Scripts

## Purpose
This repository contains R and Python workflows for spatial transcriptomics (Visium) data:
- **Quality control (QC)** of raw Visium outputs
- **Normalization & HVG selection** for downstream analysis
- **Spatial gene analysis** with nnSVG
- **Conversion** between SpatialExperiment, Seurat, AnnData, and Zarr formats
- **Image co-registration** of COMET, Ultivue, and H&E pseudo-DAPI images using VALIS


---

## Repo Structure
- `comet.py` – Preprocess COMET DAPI images
- `ultivue.py` – Preprocess Ultivue DAPI images
- `co-register_with_valis.ipynb` – VALIS-based image co-registration
- `R_QC_VScode_development.ipynb` – Detailed QC workflow for figuring stages out
- `R_QC_VScode_streamlined.ipynb` – Tidied QC workflow reduced to essental stages
- `20240206_QC_rstudio_version.Rmd` - used to figure out QC and downstream steps of spatial data before processing in ipynb/via cluster
- `submit_savetoVIPS.sh` – SLURM batch job for pyvips image export (comet.py and ultivue.py)
- `gather_*.py` – Metadata collection for COMET, Ultivue, H&E images to inform transformations applied in comet.py and ultivue.py
- `co-register_with_valis.ipynb` - notebook for co-registration of images with valis after preprocessing via comet.py/ultivue.py and submit_savetoVIPS.sh
- 

---

## Inputs
- Raw **Visium outputs** (10X SpaceRanger folders)
- Whole-slide images (COMET OME-TIFF, Ultivue TIFF, H&E SVS)
- Metadata spreadsheets

## Outputs
- QC’d `.rds` objects  
- HVG violin plots (`.png`)  
- nnSVG-processed SpatialExperiment objects (`*_nnSVG.rds`)  
- Registered pseudo-DAPI BigTIFFs  
- Error metrics and transformation pickles  

---


