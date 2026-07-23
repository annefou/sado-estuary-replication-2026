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
# # 05 — HEALPix / EOPF Zarr archive of the derived products
#
# Resamples the **derived** water-quality maps (Chl-a, SPM, turbidity) onto a
# HEALPix-NESTED grid on the **WGS84 ellipsoid** and writes them as an
# EOPF Zarr / GRID4EARTH dataset, per `DOMAIN.md` § Data formats and
# `docs/eopf-zarr-conversion.md`.
#
# ## Scope — read this before extending the notebook
#
# HEALPix is applied **only to the derived products**, never to the match-up
# extraction. The match-up path in `02`/`03` stays on the native Sentinel-2 UTM
# grid (EPSG:32631), extracting a 3×3 window at 10 m exactly as Sent et al. did.
#
# The reason is not preference, it is validity: regridding before extraction
# inserts an interpolation step into the very quantity being validated. It
# changes the effective spatial support, adds systematic bias — which
# `DOMAIN.md` tells us to minimise — and, worst of all, confounds the
# replication, because any divergence from the paper could then be the
# resampling rather than the science. Method fidelity is the point of a
# replication.
#
# What HEALPix buys, applied here, is real: equal-area cells so estuary-wide
# statistics need no area weighting, hierarchical coarsening for multiscale
# views, and a single global grid so a future Oosterschelde or Sado run lands
# in directly comparable cell IDs.

# %%
from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

import healpix_geo.nested as hn

ARCHIVE_DIR = Path("../data/archive")
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Westerschelde extent (lon/lat, WGS84) — same box used for scene discovery in 01.
WESTERSCHELDE_VERTICES = np.array(
    [[3.35, 51.30], [4.35, 51.30], [4.35, 51.58], [3.35, 51.58]]
)

# Refinement level 19 ≈ 12.4 m cells — the closest HEALPix level to Sentinel-2's
# 10 m native resolution without heavy oversampling. Level 20 (~6.2 m) is
# available if aliasing at channel edges proves a problem, at 4× the cell count.
REFINEMENT_LEVEL = 19

# GRID4EARTH convention UUIDs (docs/eopf-zarr-conversion.md).
ZARR_CONVENTIONS = [
    {"name": "multiscales", "uuid": "d35379db-88df-4056-af3a-620245f8e347"},
    {"name": "dggs", "uuid": "7b255807-140c-42ca-97f6-7a1cfecdbc38"},
]

# %% [markdown]
# ## Build the ellipsoidal HEALPix grid
#
# `ellipsoid="WGS84"` is the load-bearing argument. The default is `"sphere"`,
# which ignores flattening — over a terrestrial estuary that is a systematic
# geolocation error, exactly the kind `DOMAIN.md` says not to accept as
# "good enough". The name is case-sensitive: `"WGS84"`, not `"wgs84"`.

# %%
def build_grid(level: int = REFINEMENT_LEVEL) -> np.ndarray:
    """HEALPix-NESTED cell IDs covering the Westerschelde on the WGS84 ellipsoid."""
    cell_ids, _depths, _fully_covered = hn.polygon_coverage(
        WESTERSCHELDE_VERTICES, level, ellipsoid="WGS84"
    )
    return np.sort(cell_ids.astype("int64"))


cell_ids = build_grid()
earth_radius_m = 6_371_007.181
cell_size_m = np.sqrt(4 * np.pi * earth_radius_m**2 / (12 * 4**REFINEMENT_LEVEL))

print(f"refinement level {REFINEMENT_LEVEL} (nside {2**REFINEMENT_LEVEL})")
print(f"  nominal cell size : {cell_size_m:.2f} m")
print(f"  cells over extent : {len(cell_ids):,}")
print(f"  cell_ids memory   : {cell_ids.nbytes / 1e6:.1f} MB")

# %% [markdown]
# ## Map derived products onto the grid
#
# `03_analysis.py` writes per-scene derived maps on the native UTM grid. Each is
# resampled here by looking up the HEALPix cell containing every source pixel
# centre and averaging within cells — an area-preserving aggregation rather than
# an interpolation, which is the right operation when going from a finer
# projected grid to a coarser equal-area one.

# %%
def assign_cells(lon: np.ndarray, lat: np.ndarray, level: int = REFINEMENT_LEVEL) -> np.ndarray:
    """HEALPix-NESTED cell ID for each source pixel centre, on the WGS84 ellipsoid."""
    return hn.lonlat_to_healpix(lon, lat, level, ellipsoid="WGS84").astype("int64")


def aggregate_to_cells(values: np.ndarray, pixel_cells: np.ndarray) -> np.ndarray:
    """Mean of source pixels within each grid cell; NaN where a cell has none."""
    order = np.argsort(pixel_cells)
    sorted_cells, sorted_values = pixel_cells[order], values[order]
    unique_cells, starts = np.unique(sorted_cells, return_index=True)
    sums = np.add.reduceat(np.nan_to_num(sorted_values), starts)
    counts = np.add.reduceat(~np.isnan(sorted_values), starts)

    out = np.full(cell_ids.shape, np.nan, dtype="float32")
    positions = np.searchsorted(cell_ids, unique_cells)
    valid = (positions < cell_ids.size) & (cell_ids[np.clip(positions, 0, cell_ids.size - 1)] == unique_cells)
    with np.errstate(invalid="ignore", divide="ignore"):
        out[positions[valid]] = (sums[valid] / counts[valid]).astype("float32")
    return out


# %% [markdown]
# ## Write the EOPF Zarr / GRID4EARTH dataset

# %%
def build_dataset(
    products: dict[str, np.ndarray], times: np.ndarray, level: int = REFINEMENT_LEVEL
) -> xr.Dataset:
    """Assemble a GRID4EARTH-conformant Dataset from per-time cell arrays."""
    dataset = xr.Dataset(
        data_vars={
            name: (("time", "cells"), values.astype("float32"))
            for name, values in products.items()
        },
        coords={"cell_ids": (("cells",), cell_ids), "time": (("time",), times)},
        attrs={
            "zarr_conventions": ZARR_CONVENTIONS,
            "multiscales": {
                "layout": [
                    {
                        "asset": str(level),
                        "dggs": {
                            "name": "healpix",
                            "refinement_level": level,
                            "indexing_scheme": "nested",
                            "ellipsoid": {
                                "name": "wgs84",
                                "semimajor_axis": 6378137.0,
                                "inverse_flattening": 298.257,
                            },
                        },
                    }
                ]
            },
            "title": "Sentinel-2 derived water-quality products, Westerschelde",
            "source": "Sentinel-2 MSI L1C, atmospherically corrected (Acolite / C2RCC / Polymer)",
            "references": "https://doi.org/10.3390/rs13051043",
        },
    )
    return dataset


def write_archive(dataset: xr.Dataset, name: str, level: int = REFINEMENT_LEVEL) -> Path:
    """Write to data/archive/<name>.zarr under the multiscale group layout."""
    path = ARCHIVE_DIR / f"{name}.zarr"
    dataset.to_zarr(path, group=f"measurements/{name}/{level}", mode="w", zarr_format=3)
    return path


# %% [markdown]
# ## Status
#
# The grid construction above **runs and is verified**. The resampling and write
# steps are written but **not yet executed**, because they consume the derived
# maps from `03_analysis.py`, which needs Copernicus credentials to download the
# granules. They are wired for that input and will be run once `03` produces it.
#
# Grid sizes over the Westerschelde extent, for choosing a level later:
#
# | Level | Cell size | Cells | `cell_ids` size |
# |---|---|---|---|
# | 17 | 49.7 m | 878,571 | 7.0 MB |
# | 18 | 24.9 m | 3,507,914 | 28.1 MB |
# | **19** | **12.4 m** | **14,019,506** | **112.2 MB** |
# | 20 | 6.2 m | 56,053,774 | 448.4 MB |
#
# Counts are for the full bounding box including land; the water-only subset
# will be substantially smaller once the estuary mask from `03` is applied.

# %%
print("Grid ready. Resampling awaits derived products from 03_analysis.py.")
