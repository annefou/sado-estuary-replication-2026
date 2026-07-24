# Snakefile — orchestrates the Westerschelde replication pipeline.
#
# One rule per notebook, each executed via jupytext so the notebook stays the
# source of truth. The DAG has two halves:
#
#   data_download (01) -> data_clean (02)         credential-free, runs anywhere
#                              |                    (CI runs exactly this prefix)
#   analysis (03) -> figures (04) / archive (05)   needs the Acolite container
#                                                   AND the Sentinel-2 granules
#
# `snakemake --cores 1` runs the whole DAG — which only completes inside the
# project container (Acolite on PATH) with the granules present under
# data/raw/s2 (fetch them with scripts/fetch_granules.py). The Dockerfile CMD is
# exactly that. In plain CI, run the prep prefix only:
#
#   snakemake --cores 1 --until data_clean
#
# Granules are NOT a Snakefile rule: fetching them needs Copernicus S3
# credentials and produces many .SAFE directories, so scripts/fetch_granules.py
# owns that step. rule analysis processes whatever granules are present and skips
# scenes whose granule is missing.

NOTEBOOKS = "notebooks"


rule all:
    input:
        "figures/main_result.png",
        "results/chla_satellite_acolite.parquet",


# ---------- 01: data download (in situ + S2 scene index; no credentials) ----------
rule data_download:
    output:
        "data/raw/rws_in_situ_westerschelde.parquet",
        "data/raw/s2_l1c_scene_index.parquet",
        "data/raw/sources.json",
    log:
        "results/logs/01_data_download.log",
    shell:
        "cd {NOTEBOOKS} && jupytext --to notebook --execute 01_data_download.py 2>&1 | tee ../{log}"


# ---------- 02: match-up construction (footprint + ±2 h; no credentials) ----------
rule data_clean:
    input:
        "data/raw/rws_in_situ_westerschelde.parquet",
        "data/raw/s2_l1c_scene_index.parquet",
    output:
        "data/interim/matchups_westerschelde.parquet",
        "data/interim/matchup_summary.csv",
    log:
        "results/logs/02_data_clean.log",
    shell:
        "cd {NOTEBOOKS} && jupytext --to notebook --execute 02_data_clean.py 2>&1 | tee ../{log}"


# ---------- 03: atmospheric correction + Chl-a retrieval (CONTAINER + granules) ----------
rule analysis:
    input:
        "data/interim/matchups_westerschelde.parquet",
    output:
        "results/chla_satellite_acolite.parquet",
    log:
        "results/logs/03_analysis.log",
    shell:
        "cd {NOTEBOOKS} && jupytext --to notebook --execute 03_analysis.py 2>&1 | tee ../{log}"


# ---------- 04: figures ----------
rule figures:
    input:
        "results/chla_satellite_acolite.parquet",
    output:
        "figures/main_result.png",
    log:
        "results/logs/04_figures.log",
    shell:
        "cd {NOTEBOOKS} && jupytext --to notebook --execute 04_figures.py 2>&1 | tee ../{log}"
