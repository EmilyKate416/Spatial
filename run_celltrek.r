#!/usr/bin/env Rscript

# --- load libraries ---
library(CellTrek)
library(future)
library(future.apply)
library(progressr)
library(Seurat)

# --- parallelization ---
plan(multisession, workers = 6)           # use 6 cores
options(future.globals.maxSize = 20*1024^3)  # 20 GB per worker
handlers("txtprogressbar")  # to monitor progress

# --- logging set up ---
log_file <- "celltrek_progress"
sink(log_file, append=TRUE, split=TRUE)  #redirects console output to log file, split=TRUE keeps output visible in console while also writing to log 

# --- load your data ---
cell2loc = '/mnt/scratchc/fmlab/lythgo02/OV_visium/emily/cell2location/'

ovTraintAll <- readRDS(paste0(cell2loc, "cellTrek/ovTrainAll_obj.rds"))

seuSub <- readRDS(paste0(cell2loc, "cellTrek/seuSub.rds"))

# --- define celltrek wrapper ---
run_celltrek_fast <- function(trained_obj, sc_data, sample_name) {
  message(Sys.time(), "Processing ", sample_name) #adds timestamp to each log entry 
  
  ct_result <- CellTrek::celltrek(
    st_sc_int = trained_obj,
    int_assay = "traint",
    sc_data = sc_data,
    sc_assay = "RNA",
    reduction = "pca",
    intp = TRUE,
    intp_pnt = 3000,
    intp_lin = FALSE,
    nPCs = 20,
    dist_thresh = 0.55,
    top_spot = 5,
    spot_n = 10,
    repel_r = 25,
    repel_iter = 10,
    keep_model = TRUE,
    ntree=500
  )
  message(Sys.time(), " | Finished CellTrek for: ", sample_name)
  return(ct_result$celltrek)
}

# --- run CellTrek on all samples ---
with_progress({
  p <- progressor(along = ovTraintAll)
  
  celltrek_results <- future_lapply(
    seq_along(ovTraintAll),
    function(i) {
      sample_name <- names(ovTraintAll)[i]
      message(Sys.time(), " | Processing sample: ", sample_name)
      
      result <- run_celltrek_fast(
        trained_obj = ovTraintAll[[i]],
        sc_data = seuSub,
        sample_name = sample_name
      )
      
      saveRDS(result, file = paste0("celltrek_results", sample_name, ".rds"))
      message(Sys.time(), " | Saved result for: ", sample_name)
      
      p()  # update progress bar
      return(result)
    },
    future.stdout = TRUE
  )
})

names(celltrek_results) <- names(ovTraintAll)

saveRDS(celltrek_results, file = paste0("celltrek_results.rds"))

# --- merge results ---
merged_celltrek <- merge(celltrek_results[[1]], y = celltrek_results[-1])
merged_celltrek$treatment <- ifelse(
  merged_celltrek$orig.ident %in% c("ov_1","ov_2","ov_3"),
  "Untreated", "Treated"
)

# --- downstream co-embedding ---
DefaultAssay(merged_celltrek) <- "RNA"
merged_celltrek <- NormalizeData(merged_celltrek)
merged_celltrek <- FindVariableFeatures(merged_celltrek)
merged_celltrek <- ScaleData(merged_celltrek)
merged_celltrek <- RunPCA(merged_celltrek)
merged_celltrek <- RunUMAP(merged_celltrek, dims = 1:25)

# --- save results ---
saveRDS(merged_celltrek, "merged_celltrek.rds")
message(Sys.time(), " | CellTrek pipeline finished successfully.")

print("Complete")
# --- stop logging ---
sink()
