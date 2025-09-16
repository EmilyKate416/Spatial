#!/bin/bash
#SBATCH --job-name=celltrek
#SBATCH --partition=epyc        # request the epyc partition
#SBATCH --cpus-per-task=8       # 8 cores
#SBATCH --mem=360G              # 120 GB RAM
#SBATCH --output=celltrek_%j.log
#SBATCH --error=celltrek_%j.err

 # activate celltrek_env before submission
Rscript run_celltrek.r
