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
# 1. **Atmospheric correction** — Acolite (and Polymer, opt-in) produce
#    water-leaving reflectance `rho_w`.
# 2. **Extraction** — a 3×3 pixel window at 10 m on the native UTM grid at each
#    station, with per-pixel QC (water, cloud/shadow/glint, AC-success).
# 3. **Chl-a retrieval** — the `aGS` chain (Acolite + Gons et al. 2005), the
#    replication's anchor. (The paper selected `cGS` = C2RCC + Gons; C2RCC is
#    excluded here — see `docs/atmospheric-correction-choice.md`.)
# 4. **Agreement** — R², slope, RMSE, BIAS, APD, RPD vs the Rijkswaterstaat in
#    situ Chl-a, in log space, over the full record and the 2018–2020 subset.
#
# Everything except the atmospheric-correction step (§1) is pure Python in
# `scripts/analysis_core.py` and covered by `tests/test_analysis_core.py`.
#
# ## Atmospheric correction runs in the container
#
# The AC processors are external programs, not pip/conda libraries; this notebook
# shells out to them.
#
# | Processor | How it is invoked | In the public image? |
# |---|---|---|
# | Acolite | `acolite --cli --nogfx --settings …` | yes (GPL-3.0), pure Python |
# | Polymer | `polymer` via the opt-in pixi feature | **no** — licence; see docs |
#
# C2RCC (the original study's selected processor) is **not run**: it exists only
# inside ESA SNAP and crashes natively in-container. Excluded as a declared
# deviation — see `docs/atmospheric-correction-choice.md`.
#
# Outside the container (Acolite absent) §1 cannot run, so the notebook detects
# its absence and stops with a clear message rather than failing obscurely.
# `docs/polymer-licence-and-version.md` explains the Polymer opt-in split.

# %%
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("../scripts").resolve()))
from analysis_core import (
    chla_gons,
    coord_index,
    extract_window,
    nearest_band,
    open_acolite_l2w,
    window_reflectance,
)
from matchup_stats import stratified_statistics
from pyproj import Transformer

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
# ## Guard: is Acolite present?

# %%
def processor_available(name: str) -> bool:
    return shutil.which(name) is not None


HAVE_ACOLITE = processor_available("acolite") or Path("/opt/acolite/launch_acolite.py").exists()

print(f"Acolite available : {HAVE_ACOLITE}")
if not HAVE_ACOLITE:
    print(
        "\nAcolite is not on PATH — this notebook must run inside the project\n"
        "container (see the Dockerfile). Extraction, the Gons algorithm and the\n"
        "statistics are unit-tested separately in tests/test_analysis_core.py and\n"
        "tests/test_matchup_stats.py."
    )

# %% [markdown]
# ## 1. Atmospheric correction (container only)
#
# Acolite consumes a `.SAFE` product and writes water-leaving reflectance
# (`rhow_*`) per band into an L2W NetCDF. Driven by a settings file; the
# subprocess call keeps the notebook declarative.

# Clip Acolite to the Westerschelde. Without a limit it processes the full
# 10980x10980 tile — a ~9 GB L2W per scene, impractical over 62 scenes. This box
# (S, W, N, E) covers all six axis stations (Vlissingen 3.56 E to Schaar van
# Ouden Doel 4.25 E; 51.35–51.54 N) with margin, cutting each product to tens of MB.
ESTUARY_LIMIT = "51.30,3.45,51.58,4.35"


# %%
def run_acolite(safe_dir: Path, out_dir: Path) -> Path:
    """Atmospherically correct one scene with Acolite. Returns the output dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    settings = out_dir / "acolite_settings.txt"
    settings.write_text(
        f"inputfile={safe_dir}\n"
        f"output={out_dir}\n"
        f"limit={ESTUARY_LIMIT}\n"
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


# %% [markdown]
# ## 2 + 3. Extract windows and retrieve Chl-a
#
# `open_acolite_l2w` (in `analysis_core`, structure verified by the AC probe)
# returns a `CorrectedScene`: `rhow` bands keyed by wavelength, a validity mask
# from `l2_flags`, and the UTM `x`/`y` coordinates. The Gons chain needs 665, 705
# and 783 nm; Acolite labels the red-edge band 704, so bands are matched by
# **nearest wavelength** rather than exact name (also robust across S2A/B/C).

# %%
GONS_TARGETS_NM = (665, 705, 783)


def chla_for_scene(scene, stations: pd.DataFrame) -> pd.DataFrame:
    """Per-station Chl-a from one CorrectedScene, using the tested core."""
    # Resolve the three Gons bands once (nearest available wavelength).
    keys = {target: nearest_band(scene.rhow, target) for target in GONS_TARGETS_NM}
    band_arrays = {str(target): scene.rhow[key] for target, key in keys.items()}
    to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{scene.epsg}", always_xy=True)

    rows = []
    for station in stations.itertuples():
        easting, northing = to_utm.transform(station.lon, station.lat)
        row, col = coord_index(scene.x, scene.y, easting, northing)
        try:
            extract = extract_window(band_arrays, scene.valid, row, col)
        except ValueError:
            continue  # window runs off the scene edge -> not a match-up
        if extract.n_valid == 0:
            continue
        rho = {t: window_reflectance(extract, str(t)) for t in GONS_TARGETS_NM}
        chla = float(
            chla_gons(np.array([rho[665]]), np.array([rho[705]]), np.array([rho[783]]))[0]
        )
        rows.append(
            {
                "station": station.station,
                "time": station.time,
                "chla_satellite": chla,
                "n_valid_pixels": extract.n_valid,
                "processor": scene.processor,
            }
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
# For each match-up scene: correct with Acolite, read the L2W product into a
# `CorrectedScene`, retrieve Chl-a at each station whose in situ sample falls
# within ±2 h, then delete the corrected product (storage policy above) unless it
# is in `KEEP_FULL_SCENES`. Match-up rows are joined to the in situ Chl-a and
# scored. Gated on Acolite being present, so the notebook is import-safe outside
# the container.

# %%
def l2w_path(out_dir: Path) -> Path:
    """The single L2W NetCDF Acolite writes into a run directory."""
    hits = sorted(out_dir.glob("*_L2W.nc"))
    if not hits:
        raise FileNotFoundError(f"no *_L2W.nc in {out_dir}")
    return hits[0]


# %%
if HAVE_ACOLITE:
    matchups = pd.read_parquet(INTERIM_DIR / "matchups_westerschelde.parquet")
    chl = matchups[matchups["quantity"] == "chlorophyll_a"].copy()
    in_situ = (
        pd.read_parquet(RAW_DIR / "rws_in_situ_westerschelde.parquet")
        if (RAW_DIR := Path("../data/raw")).exists()
        else pd.DataFrame()
    )
    print(f"{chl['id'].nunique()} scenes to correct for the Acolite Chl-a chain")

    retrievals = []
    for scene in chl.drop_duplicates("id").itertuples():
        safe = next(GRANULE_DIR.rglob(f"{scene.name}"), None)
        if safe is None:
            print(f"  granule missing, skipping: {scene.name}")
            continue
        out_dir = CORRECTED_DIR / scene.id
        run_acolite(safe, out_dir)
        corrected = open_acolite_l2w(l2w_path(out_dir), processor="Acolite 20260421.0")

        # Stations whose in situ Chl-a sample pairs with THIS scene (from 02).
        scene_stations = chl[chl["id"] == scene.id][["station", "lon", "lat", "time"]]
        retrievals.append(chla_for_scene(corrected, scene_stations))

        if scene.name not in KEEP_FULL_SCENES:
            shutil.rmtree(out_dir, ignore_errors=True)  # windows kept, scene not

    satellite = pd.concat(retrievals, ignore_index=True) if retrievals else pd.DataFrame()
    satellite.to_parquet(RESULTS_DIR / "chla_satellite_acolite.parquet", index=False)
    print(f"\n{len(satellite)} satellite Chl-a retrievals -> results/chla_satellite_acolite.parquet")
else:
    print("\nSkipped §1–§4: Acolite absent. Run inside the container.")
