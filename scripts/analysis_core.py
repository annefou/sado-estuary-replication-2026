"""Pure, testable core of the analysis: window extraction, QC, bio-optical algorithms.

Separated from ``notebooks/03_analysis.py`` so it can be unit-tested without the
atmospheric-correction processors (Acolite, Polymer), which run only inside the
container. The notebook orchestrates those processors and then calls into here.

Everything in this module operates on the **native Sentinel-2 UTM grid** — no
HEALPix. Regridding belongs to the derived-product archive (notebook 05), never
to match-up extraction, because interpolating before validation would change the
quantity being validated. See DOMAIN.md and notebook 05.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Sentinel-2 MSI band centres used by the paper's algorithms (nm -> band id).
# The Gons chain uses 665 (B4), 705 (B5) and 783 (B7).
MSI_BANDS = {"B04": 665, "B05": 705, "B06": 740, "B07": 783, "B08": 842, "B8A": 865}

# 3x3 pixel window at 10 m, centred on the station — the paper's match-up support.
WINDOW = 3


@dataclass(frozen=True)
class WindowExtract:
    """A per-band 3x3 window at one station, plus the validity mask over it."""

    values: dict[str, np.ndarray]  # band id -> (3, 3) reflectance
    valid: np.ndarray  # (3, 3) bool: True where the pixel is usable
    n_valid: int


def station_rowcol(dataset, lon: float, lat: float) -> tuple[int, int]:
    """Pixel (row, col) of a lon/lat station in a rasterio dataset's own CRS.

    Kept tiny and separate so notebook 03 can call it per station without pulling
    in the whole extraction, and so it is trivially mockable in tests.
    """
    from rasterio.warp import transform

    xs, ys = transform("EPSG:4326", dataset.crs, [lon], [lat])
    return dataset.index(xs[0], ys[0])


def extract_window(
    band_arrays: dict[str, np.ndarray],
    valid_mask: np.ndarray,
    row: int,
    col: int,
    window: int = WINDOW,
) -> WindowExtract:
    """Cut the window x window block centred on (row, col) from pre-read arrays.

    ``band_arrays`` maps band id -> full 2-D reflectance array (already
    atmospherically corrected). ``valid_mask`` is the full-scene boolean validity
    mask (water AND not cloud/shadow/glint AND AC-succeeded). Taking arrays rather
    than a dataset keeps this pure and unit-testable.

    A half-open window that runs off the scene edge raises: a station whose
    support is clipped is not a valid match-up and must be dropped upstream, not
    silently padded.
    """
    half = window // 2
    r0, r1 = row - half, row + half + 1
    c0, c1 = col - half, col + half + 1

    example = next(iter(band_arrays.values()))
    if r0 < 0 or c0 < 0 or r1 > example.shape[0] or c1 > example.shape[1]:
        raise ValueError(f"window at ({row},{col}) runs off the scene edge")

    valid = np.asarray(valid_mask[r0:r1, c0:c1], dtype=bool)
    values = {band: np.asarray(arr[r0:r1, c0:c1]) for band, arr in band_arrays.items()}
    return WindowExtract(values=values, valid=valid, n_valid=int(valid.sum()))


def window_reflectance(extract: WindowExtract, band: str) -> float:
    """Mean reflectance of the valid pixels in the window for one band.

    Returns NaN if no pixel in the window is valid — the caller drops that
    match-up. The paper averages the 3x3 window; only valid pixels contribute.
    """
    if extract.n_valid == 0:
        return float("nan")
    return float(np.mean(extract.values[band][extract.valid]))


def window_product_value(extract: WindowExtract, band: str) -> float:
    """Mean of the valid **and finite** product pixels in the window; NaN if none.

    Unlike ``window_reflectance``, this skips non-finite pixels rather than letting
    one NaN poison the whole window mean. Acolite's Nechad turbidity/SPM products
    are NaN where the ``1 - rhow/C`` denominator degenerates (very bright/turbid
    pixels), so a station window can be geometrically valid yet contain NaN cells;
    those are excluded here exactly as a masked pixel would be.
    """
    if extract.n_valid == 0:
        return float("nan")
    values = extract.values[band][extract.valid]
    finite = np.isfinite(values)
    if not finite.any():
        return float("nan")
    return float(np.mean(values[finite]))


# --------------------------------------------------------------------------- #
# Corrected-scene adapter — normalises each processor's output into one shape.
#
# The probe (ac-probe.yml) revealed the real Acolite L2W layout, which this reads:
#   * dims (y, x) on the native S2 UTM grid (EPSG:32631)
#   * water-leaving reflectance bands named `rhow_<wavelength_nm>` — for S2A:
#     rhow_443/492/560/665/704/740/783/833/865/1614/2202. NOTE 704, not 705, and
#     S2B/S2C differ slightly, so bands are selected by NEAREST wavelength, never
#     by exact string.
#   * an integer `l2_flags` quality mask (0 = usable).
#   * 1-D `x` (easting) and `y` (northing) coordinates for station lookup.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CorrectedScene:
    """One atmospherically-corrected scene, processor-agnostic.

    `rhow` maps band-centre wavelength (nm) -> full 2-D reflectance array on the
    scene's UTM grid. `valid` is the full-scene usability mask. `x`/`y` are the
    1-D UTM easting/northing coordinates; `epsg` their CRS.

    `products` holds Acolite's native derived water-quality products, keyed by
    product family (e.g. ``"TUR_Nechad2009"``, ``"SPM_Nechad2010"``) then by the
    band-centre wavelength Acolite emitted (nm). These are the paper's Nechad
    turbidity / SPM algorithms, computed by Acolite with RSR-convolved published
    coefficients — the open-source ``aN`` analogue of the paper's ``cN`` chain.
    Empty for scenes corrected with ``rhow``-only settings (e.g. the Chl-a run).
    """

    rhow: dict[int, np.ndarray]
    valid: np.ndarray
    x: np.ndarray
    y: np.ndarray
    epsg: int
    processor: str
    products: dict[str, dict[int, np.ndarray]] = field(default_factory=dict)


def nearest_band(rhow: dict[int, np.ndarray], target_nm: int, *, tol_nm: int = 15) -> int:
    """Wavelength key of `rhow` closest to `target_nm`; raise if none within tol.

    Guards against silently pairing, say, a 665 nm request with an 833 nm band
    when the expected band is missing — that would be a wrong result, not a
    near-miss. Sentinel-2A vs 2B/2C band centres differ by only a few nm, so the
    default 15 nm tolerance absorbs that while rejecting genuine gaps.
    """
    if not rhow:
        raise ValueError("no rhow bands available")
    key = min(rhow, key=lambda w: abs(w - target_nm))
    if abs(key - target_nm) > tol_nm:
        raise ValueError(f"no rhow band within {tol_nm} nm of {target_nm} (nearest {key})")
    return key


def coord_index(x: np.ndarray, y: np.ndarray, easting: float, northing: float) -> tuple[int, int]:
    """(row, col) of the grid cell nearest a UTM point. row indexes y, col indexes x."""
    row = int(np.argmin(np.abs(np.asarray(y) - northing)))
    col = int(np.argmin(np.abs(np.asarray(x) - easting)))
    return row, col


def open_acolite_l2w(path, *, processor: str = "Acolite") -> CorrectedScene:
    """Read an Acolite L2W NetCDF into a CorrectedScene. I/O — covered by the
    in-container integration run, not the offline unit tests.

    l2_flags == 0 marks usable water pixels; non-finite reflectance is also
    excluded so downstream window averaging never sees a fill value.
    """
    import re

    import xarray as xr

    dataset = xr.open_dataset(path)
    rhow = {
        int(re.match(r"rhow_(\d+)", name).group(1)): dataset[name].values
        for name in dataset.data_vars
        if re.match(r"rhow_(\d+)$", name)
    }
    if not rhow:
        raise ValueError(f"{path} has no rhow_* bands — not an Acolite L2W product?")

    # Acolite's native derived products (paper's Nechad turbidity/SPM chains),
    # named e.g. TUR_Nechad2009_783 / SPM_Nechad2010_740. Band centres drift a few
    # nm between S2A/B/C (e.g. 783 vs 785), so these are keyed by the emitted
    # wavelength and selected downstream with nearest_band, exactly like rhow.
    products: dict[str, dict[int, np.ndarray]] = {}
    for name in dataset.data_vars:
        match = re.match(r"(TUR_Nechad2009|SPM_Nechad2010)_(\d+)$", name)
        if match:
            products.setdefault(match.group(1), {})[int(match.group(2))] = dataset[name].values

    flags = dataset["l2_flags"].values if "l2_flags" in dataset else np.zeros_like(
        next(iter(rhow.values())), dtype="int32"
    )
    finite = np.all([np.isfinite(band) for band in rhow.values()], axis=0)
    valid = (flags == 0) & finite

    epsg = _epsg_from_acolite(dataset)
    return CorrectedScene(
        rhow=rhow,
        valid=valid,
        x=dataset["x"].values,
        y=dataset["y"].values,
        epsg=epsg,
        processor=processor,
        products=products,
    )


def _epsg_from_acolite(dataset) -> int:
    """Best-effort EPSG from an Acolite product's UTM proj4 string; default 32631."""
    proj4 = str(dataset.attrs.get("proj4_string", ""))
    zone_match = __import__("re").search(r"zone=(\d+)", proj4)
    south = "+south" in proj4
    if zone_match:
        return (32700 if south else 32600) + int(zone_match.group(1))
    return 32631  # Westerschelde default (UTM 31N)


# --------------------------------------------------------------------------- #
# Bio-optical algorithms — transcribed from Sent et al. (2021) Table 2.
#
# These operate on rho_w (water-leaving reflectance), the output of the
# atmospheric-correction processors — NOT on TOA reflectance.
# --------------------------------------------------------------------------- #

# Gons et al. (2005) constants — reference [42] in the paper: Gons, Rijkeboer &
# Ruddick, J. Plankton Res. 27, 125-127 (2005).
#
# The two pure-water absorptions are NOT free constants: they appear as the
# literal 0.70 and 0.40 in the paper's own Table 2 equation, so they are verified
# against the paper directly.
#   aw(709) = 0.70 m^-1 ; aw(665) = 0.40 m^-1
#
# The exponent p and the specific absorption a*phy(665) are the standard Gons
# 2005 published values. Their effect on this replication differs by metric and
# is worth being precise about:
#   * a*phy(665) is a pure divisor (Chl = a_phy / a*phy), so it rescales every
#     retrieval by the same factor. R^2 is INVARIANT to it; the regression slope
#     scales by 1/a*phy; BIAS, APD and RPD DO depend on it. The paper's headline
#     asymmetry rests on R^2, which this constant cannot move — but the absolute
#     Chl-a scale and the error metrics can, so confirm against [42].
#   * p enters only the bb^p correction term; bb is small in these waters, so its
#     leverage is modest.
AW_665 = 0.40  # m^-1, pure water absorption at 665 nm (verified vs paper Table 2)
AW_709 = 0.70  # m^-1, pure water absorption at ~709 nm (verified vs paper Table 2)
GONS_ASTAR_PHY_665 = 0.0153  # m^2 mg^-1 — standard Gons value; confirm vs [42]
GONS_BACKSCATTER_EXPONENT = 1.063  # p — standard Gons value; confirm vs [42]


def chla_gons(
    rho_w_665: np.ndarray,
    rho_w_705: np.ndarray,
    rho_w_783: np.ndarray,
    *,
    astar_phy_665: float = GONS_ASTAR_PHY_665,
    p: float = GONS_BACKSCATTER_EXPONENT,
) -> np.ndarray:
    """Chlorophyll-a via Gons et al. (2005), as Table 2 states it.

        bb(783)      = 1.56 * rho_w(783) / (0.082 - 0.6 * rho_w(783))
        a_phy(665)   = (0.70 + bb) * rho_w(705)/rho_w(665) - 0.40 - bb^p
        Chl_a        = a_phy(665) / a*_phy(665)

    Note the exponent ``p`` applies ONLY to the trailing ``bb`` term; the ``bb``
    inside ``(0.70 + bb)`` is first-power. (An earlier revision wrongly raised
    both to ``p``; corrected 2026-07-23 against the algorithm's canonical form —
    aphy(665) = (0.70 + bb)*rho(705)/rho(665) - 0.40 - bb^p.)

    This is the ``cGS`` chain — the paper's selected Chl-a algorithm and this
    replication's anchor. Inputs are water-leaving reflectances at 665 (B4),
    705 (B5) and 783 (B7) nm.
    """
    rho_665 = np.asarray(rho_w_665, dtype="float64")
    rho_705 = np.asarray(rho_w_705, dtype="float64")
    rho_783 = np.asarray(rho_w_783, dtype="float64")

    backscatter = 1.56 * rho_783 / (0.082 - 0.6 * rho_783)
    a_phy_665 = (AW_709 + backscatter) * (rho_705 / rho_665) - AW_665 - backscatter**p
    return a_phy_665 / astar_phy_665
