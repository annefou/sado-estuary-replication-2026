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
    window_product_value,
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
    # rhow_* feeds the Gons Chl-a chain (aGS); the Nechad wildcards make Acolite
    # emit its native turbidity (TUR_Nechad2009_<nm>) and SPM (SPM_Nechad2010_<nm>)
    # products per band — the paper's Nechad chains, computed with Acolite's
    # RSR-convolved published coefficients (the open-source `aN` analogue of `cN`).
    settings.write_text(
        f"inputfile={safe_dir}\n"
        f"output={out_dir}\n"
        f"limit={ESTUARY_LIMIT}\n"
        "l2w_parameters=rhow_*,tur_nechad2009_*,spm_nechad2010_*\n"
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
# ## 2 + 3. Extract windows and retrieve the three parameters
#
# `open_acolite_l2w` (in `analysis_core`, structure verified by the AC probe)
# returns a `CorrectedScene`: `rhow` bands keyed by wavelength, the native Nechad
# `products` (turbidity/SPM), a validity mask from `l2_flags`, and the UTM `x`/`y`
# coordinates. The Gons chain needs 665, 705 and 783 nm; Acolite labels the
# red-edge band 704 (and drifts a few nm across S2A/B/C), so bands are matched by
# **nearest wavelength** rather than exact name — for `rhow` and for the products.
#
# Three parameters are retrieved, one per limb of the paper's asymmetry claim:
#
# | Parameter | Chain | Band | Paper's selected chain |
# |---|---|---|---|
# | Chlorophyll-a | Acolite + Gons 2005 (`aGS`) | 665/705/783 | `cGS` (C2RCC), R²=0.63 |
# | Turbidity | Acolite + Nechad 2009 (`aN783`) | 783 nm | `cN783`, R²=0.84 |
# | SPM | Acolite + Nechad 2010 (`aN740`) | 740 nm | `cN740`, R²=0.49 |

# %%
GONS_TARGETS_NM = (665, 705, 783)

# The paper's selected Nechad bands: turbidity at 783 nm (cN783), SPM at 740 nm
# (cN740). Nearest-wavelength matching absorbs the S2A/B/C band-centre drift.
TURBIDITY_TARGET_NM = 783
SPM_TARGET_NM = 740


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


def product_for_scene(
    scene, stations: pd.DataFrame, product_name: str, target_nm: int
) -> pd.DataFrame:
    """Per-station value of one native Acolite product (turbidity/SPM) from a scene.

    Mirrors `chla_for_scene` but reads a pre-computed Nechad product band instead
    of running a bio-optical algorithm: select the band nearest `target_nm`, cut
    the 3x3 window at each station, and average the valid, finite pixels.
    """
    if product_name not in scene.products or not scene.products[product_name]:
        return pd.DataFrame()  # scene corrected without this product
    key = nearest_band(scene.products[product_name], target_nm)
    band_arrays = {product_name: scene.products[product_name][key]}
    to_utm = Transformer.from_crs("EPSG:4326", f"EPSG:{scene.epsg}", always_xy=True)

    rows = []
    for station in stations.itertuples():
        easting, northing = to_utm.transform(station.lon, station.lat)
        row, col = coord_index(scene.x, scene.y, easting, northing)
        try:
            extract = extract_window(band_arrays, scene.valid, row, col)
        except ValueError:
            continue  # window runs off the scene edge -> not a match-up
        value = window_product_value(extract, product_name)
        if not np.isfinite(value):
            continue
        rows.append(
            {
                "station": station.station,
                "time": station.time,
                "value_satellite": float(value),
                "n_valid_pixels": extract.n_valid,
                "band_nm": int(key),
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
# ## Driver — resumable, per-(scene, parameter) checkpointed
#
# One Acolite correction per scene feeds all three parameters (the correction is
# the expensive step; extracting three products from it is nearly free). For each
# match-up scene we correct once, then retrieve every parameter that has an in situ
# sample pairing with that scene, writing **one checkpoint per parameter** to
# `results/partial/<parameter>/<id>.parquet`.
#
# Checkpointing per (scene, parameter) makes the run **resumable at that grain**: a
# scene is corrected only if *some* parameter still needs it, and each parameter is
# extracted only if its own checkpoint is missing. So the Chl-a checkpoints from the
# earlier run are reused as-is (not recomputed), and an interrupted run loses at most
# the scene in flight. Each parameter's final parquet is the concatenation of its
# checkpoints. Gated on Acolite being present, so the notebook is import-safe.

# %%
PARTIAL_DIR = RESULTS_DIR / "partial"
PARTIAL_DIR.mkdir(parents=True, exist_ok=True)

# The three limbs of the paper's asymmetry claim. `extract` is called with
# (CorrectedScene, stations) and returns a per-station retrieval frame; `output`
# is the final concatenated parquet each figure/stats step reads.
QUANTITY_SPECS = {
    "chlorophyll_a": {
        "extract": lambda scene, st: chla_for_scene(scene, st),
        "output": "chla_satellite_acolite.parquet",
    },
    "turbidity": {
        "extract": lambda scene, st: product_for_scene(scene, st, "TUR_Nechad2009", TURBIDITY_TARGET_NM),
        "output": "turbidity_satellite_acolite.parquet",
    },
    "spm": {
        "extract": lambda scene, st: product_for_scene(scene, st, "SPM_Nechad2010", SPM_TARGET_NM),
        "output": "spm_satellite_acolite.parquet",
    },
}


def l2w_path(out_dir: Path) -> Path:
    """The single L2W NetCDF Acolite writes into a run directory."""
    hits = sorted(out_dir.glob("*_L2W.nc"))
    if not hits:
        raise FileNotFoundError(f"no *_L2W.nc in {out_dir}")
    return hits[0]


def _migrate_flat_chla_partials(partial_dir: Path) -> None:
    """Move the earlier run's flat `partial/<id>.parquet` Chl-a checkpoints into
    the per-parameter `partial/chlorophyll_a/` layout, so they are reused, not
    recomputed. One-shot and idempotent."""
    chla_dir = partial_dir / "chlorophyll_a"
    chla_dir.mkdir(parents=True, exist_ok=True)
    for p in partial_dir.glob("*.parquet"):  # flat files = old Chl-a checkpoints
        target = chla_dir / p.name
        if not target.exists():
            p.rename(target)
        else:
            p.unlink()


# %%
if HAVE_ACOLITE:
    _migrate_flat_chla_partials(PARTIAL_DIR)
    matchups = pd.read_parquet(INTERIM_DIR / "matchups_westerschelde.parquet")

    # Per-parameter match-up rows and checkpoint dirs; scenes = union across params.
    rows_by_q = {q: matchups[matchups["quantity"] == q].copy() for q in QUANTITY_SPECS}
    scene_ids_by_q = {q: set(rows_by_q[q]["id"]) for q in QUANTITY_SPECS}
    pdir_by_q = {q: PARTIAL_DIR / q for q in QUANTITY_SPECS}
    for d in pdir_by_q.values():
        d.mkdir(parents=True, exist_ok=True)

    scenes = matchups[matchups["quantity"].isin(QUANTITY_SPECS)].drop_duplicates("id")
    done = {q: sum(1 for _ in pdir_by_q[q].glob("*.parquet")) for q in QUANTITY_SPECS}
    print(f"{len(scenes)} scenes across {list(QUANTITY_SPECS)}; checkpointed so far: {done}")

    for n, scene in enumerate(scenes.itertuples(), start=1):
        # Which parameters does this scene serve, and still lack a checkpoint for?
        todo = [
            q for q in QUANTITY_SPECS
            if scene.id in scene_ids_by_q[q]
            and not (pdir_by_q[q] / f"{scene.id}.parquet").exists()
        ]
        if not todo:
            continue
        safe = next(GRANULE_DIR.rglob(f"{scene.name}"), None)
        if safe is None:
            print(f"  [{n}/{len(scenes)}] granule missing, skipping: {scene.name}", flush=True)
            continue
        out_dir = CORRECTED_DIR / scene.id
        try:
            run_acolite(safe, out_dir)
            corrected = open_acolite_l2w(l2w_path(out_dir), processor="Acolite 20260421.0")
            counts = {}
            for q in todo:
                stations = rows_by_q[q][rows_by_q[q]["id"] == scene.id][["station", "lon", "lat", "time"]]
                result = QUANTITY_SPECS[q]["extract"](corrected, stations)
                # Atomic checkpoint: temp then rename, so a kill mid-write cannot
                # leave a truncated partial that resume would trust.
                tmp = pdir_by_q[q] / f".{scene.id}.tmp.parquet"
                result.to_parquet(tmp, index=False)
                tmp.rename(pdir_by_q[q] / f"{scene.id}.parquet")
                counts[q] = len(result)
            print(f"  [{n}/{len(scenes)}] {scene.name}: {counts}", flush=True)
        except Exception as exc:  # one bad scene must not abort the whole run
            print(f"  [{n}/{len(scenes)}] FAILED {scene.name}: {type(exc).__name__}: {exc}", flush=True)
        finally:
            if scene.name not in KEEP_FULL_SCENES:
                shutil.rmtree(out_dir, ignore_errors=True)  # windows kept, scene not

    # Concatenate each parameter's checkpoints into its final result.
    for q, spec in QUANTITY_SPECS.items():
        parts = [pd.read_parquet(p) for p in sorted(pdir_by_q[q].glob("*.parquet"))]
        combined = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        combined.to_parquet(RESULTS_DIR / spec["output"], index=False)
        print(f"{len(combined):4d} {q} retrievals from {len(parts)} scenes -> results/{spec['output']}")
else:
    print("\nSkipped §1–§4: Acolite absent. Run inside the container.")
