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
# # 05 — HEALPix / DGGS Zarr archive of the derived products
#
# Resamples the **derived** water-quality products (Chl-a, SPM, turbidity) onto a
# HEALPix grid on the WGS84 ellipsoid and writes them in the **GRID4EARTH DGGS
# Zarr convention**, per `DOMAIN.md` § Data formats and
# `docs/eopf-zarr-conversion.md`.
#
# ## Terminology — follow GRID4EARTH, not ad-hoc names
#
# The GRID4EARTH stack has settled vocabulary and this notebook uses it verbatim,
# so the archive is readable by `xdggs`, `healpix-resample` and the converters
# without translation:
#
# | GRID4EARTH term | Meaning | Do **not** call it |
# |---|---|---|
# | `refinement_level` | HEALPix resolution level | "level", "order", "nside", "depth" |
# | `indexing_scheme` | `"nested"` here, always | "ordering", "scheme", "NEST" |
# | `ellipsoid` | `{"name": "wgs84"}` | "datum", "CRS", "sphere" |
# | `cell_ids` | int64 coordinate of HEALPix cell identifiers | "pixel ids", "hpx index" |
# | `cells` | the spatial dimension | "pixel", "npix" |
#
# `nside` is a `healpy`-era name and does not appear in GRID4EARTH metadata;
# where a library needs it, derive it locally as `2**refinement_level` rather
# than storing or reporting it.
#
# ## Scope — HEALPix applies to derived products only
#
# The match-up extraction in `02`/`03` stays on the native Sentinel-2 UTM grid
# (EPSG:32631), taking a 3×3 window at 10 m exactly as Sent et al. did.
# Resampling before extraction would insert an interpolation step into the very
# quantity being validated, change the effective spatial support, add systematic
# bias — which `DOMAIN.md` says to minimise — and confound the replication,
# because any divergence from the paper could then be the resampling rather than
# the science. Method fidelity is the point of a replication.
#
# Applied *here*, to the derived products, HEALPix earns its place: equal-area
# cells so estuary-wide statistics need no area weighting, lossless hierarchical
# coarsening, and a single global grid so a future Oosterschelde or Sado run
# lands in directly comparable `cell_ids`.

# %%
from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

import healpix_geo.nested as hpx

ARCHIVE_DIR = Path("../data/archive")
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Westerschelde extent (lon/lat, WGS84) — the box used for scene discovery in 01.
WESTERSCHELDE_VERTICES = np.array(
    [[3.35, 51.30], [4.35, 51.30], [4.35, 51.58], [3.35, 51.58]]
)

# Refinement level 19 ≈ 12.4 m cells, the closest HEALPix resolution to
# Sentinel-2's 10 m without heavy oversampling. GRID4EARTH's own Sentinel-2
# converter settings ship presets at refinement levels 17, 19 and 20, so this
# sits on a level the ecosystem already expects.
REFINEMENT_LEVEL = 19
INDEXING_SCHEME = "nested"
ELLIPSOID = {"name": "wgs84", "semimajor_axis": 6378137.0, "inverse_flattening": 298.257}

# GRID4EARTH convention UUIDs (docs/eopf-zarr-conversion.md).
ZARR_CONVENTIONS = [
    {"name": "multiscales", "uuid": "d35379db-88df-4056-af3a-620245f8e347"},
    {"name": "dggs", "uuid": "7b255807-140c-42ca-97f6-7a1cfecdbc38"},
]

# %% [markdown]
# ## Build the ellipsoidal HEALPix grid
#
# `ellipsoid="WGS84"` is the load-bearing argument. The `healpix-geo` default is
# `"sphere"`, which ignores flattening — over a terrestrial estuary that is a
# systematic geolocation error, exactly the kind `DOMAIN.md` refuses to accept as
# "good enough". Note the argument value is **case-sensitive** (`"WGS84"`), while
# the GRID4EARTH *metadata* spells the ellipsoid name lowercase (`"wgs84"`).

# %%
def build_cell_ids(refinement_level: int = REFINEMENT_LEVEL) -> np.ndarray:
    """HEALPix-nested cell_ids covering the Westerschelde on the WGS84 ellipsoid."""
    cell_ids, _refinement_levels, _fully_covered = hpx.polygon_coverage(
        WESTERSCHELDE_VERTICES, refinement_level, ellipsoid="WGS84"
    )
    return np.sort(cell_ids.astype("int64"))


cell_ids = build_cell_ids()

authalic_radius_m = 6_371_007.181
cell_size_m = np.sqrt(4 * np.pi * authalic_radius_m**2 / (12 * 4**REFINEMENT_LEVEL))

print(f"refinement_level  : {REFINEMENT_LEVEL}")
print(f"indexing_scheme   : {INDEXING_SCHEME}")
print(f"ellipsoid         : {ELLIPSOID['name']}")
print(f"nominal cell size : {cell_size_m:.2f} m")
print(f"cells over extent : {len(cell_ids):,}")
print(f"cell_ids memory   : {cell_ids.nbytes / 1e6:.1f} MB")

# %% [markdown]
# ## Resample derived products onto the grid
#
# Use `healpix-resample` rather than hand-rolled aggregation: it manages the
# HEALPix authalic definition and the WGS84 ellipsoid itself, and offers the
# resampling strategies GRID4EARTH standardises on — `NearestResampler`,
# `BilinearResampler`, `KNeighborsResampler`, `PSFResampler`, `CellPointResampler`.
#
# For going from a *finer* projected grid (10 m Sentinel-2) to a *coarser*
# equal-area target (12.4 m cells), `CellPointResampler` is the right default: it
# groups source points by target cell and averages within them, which preserves
# the areal mean instead of interpolating. `PSFResampler` is the option to reach
# for if point-spread effects matter for a specific product.
#
# `legacy-converters` (GRID4EARTH) is the production path for converting whole
# Sentinel-2 products, but it consumes **EOPF-compliant Zarr** input, whereas our
# atmospheric-correction chain consumes `.SAFE` and emits our own derived arrays.
# So we reuse its *conventions* (below) and `healpix-resample` for the regridding,
# rather than the converter itself.

# %%
def resample_to_cells(
    lon: np.ndarray,
    lat: np.ndarray,
    values: np.ndarray,
    refinement_level: int = REFINEMENT_LEVEL,
) -> np.ndarray:
    """Areal-mean resampling of scattered (lon, lat, value) onto the cell grid."""
    from healpix_resample import CellPointResampler

    resampler = CellPointResampler(
        refinement_level=refinement_level, indexing_scheme=INDEXING_SCHEME
    )
    result = resampler(lon=lon, lat=lat, data=values, target_cell_ids=cell_ids)
    return np.asarray(result.data, dtype="float32")


# %% [markdown]
# ## Write the GRID4EARTH DGGS Zarr dataset

# %%
def build_dataset(
    products: dict[str, np.ndarray],
    times: np.ndarray,
    refinement_level: int = REFINEMENT_LEVEL,
) -> xr.Dataset:
    """Assemble a DGGS-Zarr-conformant Dataset from per-time cell arrays."""
    return xr.Dataset(
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
                        "asset": str(refinement_level),
                        "dggs": {
                            "name": "healpix",
                            "refinement_level": refinement_level,
                            "indexing_scheme": INDEXING_SCHEME,
                            "ellipsoid": ELLIPSOID,
                        },
                    }
                ]
            },
            "title": "Sentinel-2 derived water-quality products, Westerschelde",
            "source": "Sentinel-2 MSI L1C, atmospherically corrected (Acolite / C2RCC / Polymer)",
            "references": "https://doi.org/10.3390/rs13051043",
        },
    )


def write_archive(
    dataset: xr.Dataset, name: str, refinement_level: int = REFINEMENT_LEVEL
) -> Path:
    """Write under the multiscale group layout: measurements/<name>/<refinement_level>."""
    path = ARCHIVE_DIR / f"{name}.zarr"
    dataset.to_zarr(
        path, group=f"measurements/{name}/{refinement_level}", mode="w", zarr_format=3
    )
    return path


# %% [markdown]
# ## Status
#
# Grid construction above **runs and is verified**. Resampling and write are
# written but **not yet executed** — they consume the derived products from
# `03_analysis.py`, which is still being built.
#
# Grid sizes over the Westerschelde extent, for choosing a refinement level:
#
# | `refinement_level` | Cell size | Cells | `cell_ids` size |
# |---|---|---|---|
# | 17 | 49.7 m | 878,571 | 7.0 MB |
# | 18 | 24.9 m | 3,507,914 | 28.1 MB |
# | **19** | **12.4 m** | **14,019,506** | **112.2 MB** |
# | 20 | 6.2 m | 56,053,774 | 448.4 MB |
#
# Counts cover the full bounding box including land; the water-only subset will
# be substantially smaller once the estuary mask from `03` is applied.

# %%
print("Grid ready. Resampling awaits derived products from 03_analysis.py.")
