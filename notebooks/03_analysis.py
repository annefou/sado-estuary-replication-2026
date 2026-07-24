# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 03 — Analysis: atmospheric correction, extraction, Chl-a retrieval, agreement
#
# Ports Sent et al. (2021) faithfully, with deviations flagged. For each match-up
# scene from `02`:
#
# 1. **Atmospheric correction** — Acolite and C2RCC (and Polymer, opt-in) produce
#    water-leaving reflectance `rho_w`.
# 2. **Extraction** — a 3×3 pixel window at 10 m on the native UTM grid at each
#    station, with per-pixel QC (water, cloud/shadow/glint, AC-success).
# 3. **Chl-a retrieval** — the `cGS` chain (C2RCC + Gons et al. 2005), the
#    replication's anchor.
# 4. **Agreement** — R², slope, RMSE, BIAS, APD, RPD vs the Rijkswaterstaat in
#    situ Chl-a, in log space, over the full record and the 2018–2020 subset.
#
# Everything except the atmospheric-correction step (§1) is pure Python in
# `scripts/analysis_core.py` and covered by `tests/test_analysis_core.py`.
#
# ## Everything runs in the container
#
# The atmospheric-correction processors are **not** pip/conda-installable Python
# libraries — they are external programs. This notebook shells out to them, and
# the `Dockerfile` is what provides them:
#
# | Processor | How it is invoked | In the image? |
# |---|---|---|
# | Acolite | `python acolite --cli --settings …` | yes (GPL-3.0) |
# | C2RCC | ESA SNAP `gpt <graph.xml>` | yes (SNAP, GPL-3.0) |
# | Polymer | `polymer` via the opt-in pixi feature | **no** — licence; see docs |
#
# Outside the container (SNAP and Acolite absent) §1 cannot run, so the notebook
# detects their absence and stops with a clear message rather than failing
# obscurely. `docs/polymer-licence-and-version.md` explains the Polymer split.

# %%
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("../scripts").resolve()))
from analysis_core import chla_gons, extract_window, station_rowcol, window_reflectance
from matchup_stats import stratified_statistics

INTERIM_DIR = Path("../data/interim")
GRANULE_DIR = Path("../data/raw/s2")
CORRECTED_DIR = Path("../data/interim/corrected")  # transient; windows kept, scenes not
RESULTS_DIR = Path("../results")
for directory in (CORRECTED_DIR, RESULTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Storage policy (decided 2026-07-23): extract the 3×3 windows immediately after
# correcting each scene, then delete the full corrected scene. Three processors ×
# 62 scenes of full corrected output would be hundreds of GB for no benefit —
# only the 3×3 windows feed the statistics. A short allow-list of scenes is kept
# in full for the estuary-wide maps in notebook 05.
KEEP_FULL_SCENES: set[str] = set()  # populated once the map scenes are chosen

# %% [markdown]
# ## Guard: are the correction processors present?

# %%
def processor_available(name: str) -> bool:
    return shutil.which(name) is not None


HAVE_ACOLITE = processor_available("acolite") or Path("/opt/acolite/launch_acolite.py").exists()
HAVE_GPT = processor_available("gpt")  # ESA SNAP graph processing tool

print(f"Acolite available : {HAVE_ACOLITE}")
print(f"SNAP gpt available: {HAVE_GPT}")
if not (HAVE_ACOLITE and HAVE_GPT):
    print(
        "\nAtmospheric-correction processors are not on PATH — this notebook must run\n"
        "inside the project container (see the Dockerfile). Extraction, the Gons\n"
        "algorithm and the statistics are unit-tested separately in\n"
        "tests/test_analysis_core.py and tests/test_matchup_stats.py."
    )

# %% [markdown]
# ## 1. Atmospheric correction (container only)
#
# Each processor consumes a `.SAFE` product and writes `rho_w` per band. Acolite
# is driven by a settings file; C2RCC by a SNAP graph passed to `gpt`. Both are
# subprocess calls so the notebook stays declarative and the heavy lifting is the
# external program's.

# %%
def run_acolite(safe_dir: Path, out_dir: Path) -> Path:
    """Atmospherically correct one scene with Acolite. Returns the output dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    settings = out_dir / "acolite_settings.txt"
    settings.write_text(
        f"inputfile={safe_dir}\n"
        f"output={out_dir}\n"
        "l2w_parameters=rhow_*\n"
        "s2_target_res=10\n"
    )
    # --nogfx skips the matplotlib import entirely (verified against
    # launch_acolite.py at tag 20260421.0) — cleaner and safer for a headless
    # container than relying on the Agg-backend fallback.
    subprocess.run(
        ["acolite", "--cli", "--nogfx", "--settings", str(settings)],
        check=True,
        capture_output=True,
    )
    return out_dir


# C2RCC needs a scene salinity and temperature. The Westerschelde gradient is
# large, so passing per-scene values (from the nearest-in-time Rijkswaterstaat
# measurement) beats a single default. These fall back to estuarine averages when
# no in situ value is available for a scene.
DEFAULT_SALINITY = 20.0  # practical salinity — estuary-axis average
DEFAULT_TEMPERATURE = 12.0  # deg C — annual mean; refine per-scene where possible


def run_c2rcc(
    safe_dir: Path,
    out_dir: Path,
    *,
    salinity: float = DEFAULT_SALINITY,
    temperature: float = DEFAULT_TEMPERATURE,
    graph: Path = Path("../scripts/c2rcc_graph.xml"),
) -> Path:
    """Atmospherically correct one scene with C2RCC via SNAP gpt."""
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "c2rcc.nc"
    subprocess.run(
        [
            "gpt", str(graph),
            f"-Pinput={safe_dir}",
            f"-Poutput={target}",
            f"-Psalinity={salinity}",
            f"-Ptemperature={temperature}",
        ],
        check=True,
        capture_output=True,
    )
    return target


# %% [markdown]
# ## 2 + 3. Extract windows and retrieve Chl-a
#
# `open_corrected` returns, per band, the full `rho_w` array plus a validity mask
# (water AND not cloud/shadow/glint AND AC-succeeded). Reading corrected output is
# processor-specific; that adapter lives with the processor call and is stubbed
# here until the container run wires it.

# %%
def chla_for_scene(corrected, stations: pd.DataFrame) -> pd.DataFrame:
    """Per-station Chl-a from one corrected scene, using the tested core."""
    band_arrays, valid_mask, dataset = corrected  # from the processor adapter
    rows = []
    for station in stations.itertuples():
        try:
            row, col = station_rowcol(dataset, station.lon, station.lat)
            extract = extract_window(band_arrays, valid_mask, row, col)
        except ValueError:
            continue  # off-edge or unreadable -> not a match-up
        if extract.n_valid == 0:
            continue
        rho = {b: window_reflectance(extract, b) for b in ("B04", "B05", "B07")}
        chla = float(
            chla_gons(np.array([rho["B04"]]), np.array([rho["B05"]]), np.array([rho["B07"]]))[0]
        )
        rows.append(
            {"station": station.station, "chla_satellite": chla, "n_valid_pixels": extract.n_valid}
        )
    return pd.DataFrame(rows)


# %% [markdown]
# ## 4. Agreement statistics
#
# Matched satellite Chl-a is joined to the in situ Chl-a on (station, time) and
# scored with `stratified_statistics(..., log=True)` — regression metrics in log
# space, APD/RPD linear, per the paper. Reporting the full record **and** the
# 2018–2020 subset is the agreed mitigation for the site/period confound: this
# replication changed both, and neither number alone separates them
# (`nanopubs/drafts/00b_in_situ_source_scan.md`).

# %%
def score(matched: pd.DataFrame) -> dict:
    """Agreement of matched satellite vs in situ Chl-a, full record and subset."""
    stats = stratified_statistics(
        matched["chla_satellite"].to_numpy(),
        matched["chla_in_situ"].to_numpy(),
        matched["time"].to_numpy(),
        log=True,
    )
    return {window: metric.as_dict() for window, metric in stats.items()}


# %% [markdown]
# ## Driver
#
# Wired but gated on the processors being present. The per-processor corrected-
# output adapter (`open_corrected`) is the remaining container-only piece; it is
# written during the first in-container run, when the exact Acolite / C2RCC output
# layout can be read from a real product rather than guessed.

# %%
if HAVE_ACOLITE and HAVE_GPT:
    matchups = pd.read_parquet(INTERIM_DIR / "matchups_westerschelde.parquet")
    chl_matchups = matchups[matchups["quantity"] == "chlorophyll_a"]
    print(f"{chl_matchups['id'].nunique()} scenes to correct for the Chl-a chain")
    # for scene in chl_matchups.drop_duplicates("id").itertuples():
    #     safe = GRANULE_DIR / ... ; corrected = run_c2rcc(safe, CORRECTED_DIR / scene.id)
    #     ... extract windows, then delete corrected unless scene.name in KEEP_FULL_SCENES
    raise NotImplementedError(
        "Container run: wire open_corrected() to the C2RCC/Acolite output layout, "
        "then loop over scenes. All downstream functions are tested."
    )
else:
    print("\nSkipped §1–§4: correction processors absent. Run inside the container.")
