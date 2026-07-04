# Repo reserves bare `rv`/`rv.exe` on PATH for the Ruby version manager (spinel-coop).
# A2-ai's R package manager (also named rv.exe) is installed to an isolated
# root instead — but rv-r's own auto-generated rv/scripts/{activate,rvr}.R
# call bare "rv"/"rv.exe" via system2()/Sys.which(), which would otherwise
# resolve to Ruby's rv on PATH. Prepending the isolated root here is scoped
# to this R session's own PATH only — it does not touch the parent shell or
# any other process, so Ruby's `rv` resolution elsewhere is unaffected.
r_rv_bin_dir <- file.path(Sys.getenv("USERPROFILE"), ".r-rv", "bin")
if (dir.exists(r_rv_bin_dir)) {
	Sys.setenv(PATH = paste(r_rv_bin_dir, Sys.getenv("PATH"), sep = .Platform$path.sep))
}

source("rv/scripts/rvr.R")
source("rv/scripts/activate.R")
