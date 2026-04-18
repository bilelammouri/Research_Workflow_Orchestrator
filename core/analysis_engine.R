# analysis_engine.R
# Resilient Bibliometric Analysis (Binary Mode)

# Setup library path
local_libs <- file.path(getwd(), "..", "R_libs")
dir.create(local_libs, showWarnings = FALSE)
.libPaths(c(local_libs, .libPaths()))

# Function to install safely
safe_install <- function(pkg) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    cat(paste0("[R] Installing ", pkg, " (Binary)... \n"))
    # Forced Binary installation to avoid C++ compilation errors on Windows
    install.packages(pkg, repos = "https://cloud.r-project.org", lib = local_libs, type = "win.binary")
  }
}

tryCatch({
  safe_install("bibliometrix")
  library(bibliometrix)
}, error = function(e) {
  cat("[R Error] Bibliometrix installation failed. Check internet connection.\n")
})

if (file.exists("results.bib") && file.size("results.bib") > 0) {
    cat("[R] Loading results.bib...\n")
    M <- tryCatch({
        convert2df(file = "results.bib", dbsource = "scopus", format = "bibtex")
    }, error = function(e) { NULL })

    if (!is.null(M) && nrow(M) > 0) {
        cat("[R] Performing analysis...\n")
        res <- biblioAnalysis(M)
        
        # 1. Visualization (Wrapped in try to prevent halt)
        try({
            png("bibliometric_summary.png", width=1200, height=1000, res=150)
            plot(x = res, k = 10, pause = FALSE)
            dev.off()
        })
        
        # 2. Extract Ranking Data
        ranking <- M[, c("TI", "AU", "PY", "TC", "DI"), drop = FALSE]
        write.csv(ranking, "citation_metrics.csv", row.names = FALSE)
        
        cat("[R] Analysis complete.\n")
    } else {
        cat("[R] Result set empty, skipping plots.\n")
    }
} else {
    cat("[R] results.bib missing or empty.\n")
}
