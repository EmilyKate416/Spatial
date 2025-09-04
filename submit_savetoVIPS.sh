#!/bin/bash
# ------------------------------------------------------------------------------
# Purpose
# ------------------------------------------------------------------------------
# SLURM batch script to run COMET or Ultivue image preprocessing (`comet.py` or 'ultivue.py') on the cluster.
# Sets up micromamba environment, applies required libvips/libffi paths, and
# executes the Python workflow in the napari-env.
# ------------------------------------------------------------------------------
#SBATCH --job-name=lay1_job
#SBATCH --output=lay1.log
#SBATCH --error=lay1_error.log
#SBATCH --partition=rocm
#SBATCH --cpus-per-task=8
#SBATCH --mem=258G
#SBATCH --time=48:00:00   # (Adjust depending on how long your job takes)

# Initialize micromamba shell support (IMPORTANT for batch jobs)
eval "$(micromamba shell hook --shell bash)"

# Activate your micromamba env (optional)
micromamba activate napari-env


# Load your environment variables *here*
export PATH="$HOME/local/libvips/bin:$PATH"
export PKG_CONFIG_PATH="$HOME/local/libvips/lib64/pkgconfig:$PKG_CONFIG_PATH"
export LD_LIBRARY_PATH="$HOME/local/libvips/lib64:/home/lythgo02/micromamba/pkgs/libffi-3.4.6-h2dba641_1/lib:/home/lythgo02/micromamba/envs/napari-env/lib:$LD_LIBRARY_PATH"


# Run the script
python /mnt/scratchc/fmlab/lythgo02/Spatial/scripts/comet.py

#python /mnt/scratchc/fmlab/lythgo02/Spatial/scripts/ultivue.py