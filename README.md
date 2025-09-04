
# Spatial QC and Registration Scripts

## Purpose
This repository contains R and Python workflows for spatial transcriptomics (Visium) data:
- **Conversion** between SpatialExperiment, Seurat, AnnData, and Zarr formats
- **Image co-registration** of COMET, Ultivue, and H&E pseudo-DAPI images using VALIS
- **Cell2location** and downstream workflows


---

## Repo Structure
- `comet.py` – Preprocess COMET DAPI images
- `ultivue.py` – Preprocess Ultivue DAPI images
- `co-register_with_valis.ipynb` – VALIS-based image co-registration
- `submit_savetoVIPS.sh` – SLURM batch job for pyvips image export (comet.py and ultivue.py)
- `gather_*.py` – Metadata collection for COMET, Ultivue, H&E images to inform transformations applied in comet.py and ultivue.py
- `co-register_with_valis.ipynb` - notebook for co-registration of images with valis after preprocessing via comet.py/ultivue.py and submit_savetoVIPS.sh
- `human_visium_run_cell2location.ipynb` - notebook for running cell2location on my visium samples
- `prepare_scRNAseq_cell2location.ipynb` - notebook for preprocessing of single cell RNA reference dataset prior to running cell2location
---



