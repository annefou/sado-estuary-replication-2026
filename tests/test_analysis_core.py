"""Tests for the pure analysis core: window extraction, QC, and the Gons algorithm.

These run without any atmospheric-correction processor, so they exercise the
science that is testable outside the container.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from analysis_core import (  # noqa: E402
    GONS_ASTAR_PHY_665,
    chla_gons,
    coord_index,
    extract_window,
    nearest_band,
    window_reflectance,
)


# --- Corrected-scene adapter helpers (Acolite L2W layout from the probe) ---

def test_nearest_band_picks_704_for_705_request():
    # Acolite labels the S2 red-edge band 704, the paper's algorithm asks for 705.
    rhow = {665: None, 704: None, 740: None, 783: None}
    assert nearest_band(rhow, 705) == 704
    assert nearest_band(rhow, 665) == 665
    assert nearest_band(rhow, 783) == 783


def test_nearest_band_rejects_when_no_band_in_tolerance():
    rhow = {443: None, 833: None, 2202: None}
    with pytest.raises(ValueError, match="within 15 nm of 665"):
        nearest_band(rhow, 665)


def test_nearest_band_empty_raises():
    with pytest.raises(ValueError, match="no rhow bands"):
        nearest_band({}, 665)


def test_coord_index_finds_nearest_cell():
    x = np.array([568090.0, 568100.0, 568110.0, 568120.0])  # easting, 10 m steps
    y = np.array([5700390.0, 5700380.0, 5700370.0])  # northing, decreasing
    # A point closest to x=568110 (col 2), y=5700380 (row 1)
    row, col = coord_index(x, y, easting=568108.0, northing=5700381.0)
    assert (row, col) == (1, 2)


def _bands(fill: float, shape=(10, 10)) -> dict[str, np.ndarray]:
    return {b: np.full(shape, fill, dtype="float32") for b in ("B04", "B05", "B07")}


def test_extract_window_is_centred_and_3x3():
    bands = {"B04": np.arange(100, dtype="float32").reshape(10, 10)}
    valid = np.ones((10, 10), dtype=bool)
    extract = extract_window(bands, valid, row=5, col=5)
    assert extract.values["B04"].shape == (3, 3)
    # centre pixel is row*10+col = 55, corners are 44 and 66
    assert extract.values["B04"][1, 1] == 55
    assert extract.values["B04"][0, 0] == 44
    assert extract.values["B04"][2, 2] == 66


def test_extract_window_off_edge_raises():
    bands = _bands(1.0)
    valid = np.ones((10, 10), dtype=bool)
    with pytest.raises(ValueError, match="off the scene edge"):
        extract_window(bands, valid, row=0, col=0)  # top-left corner has no 3x3


def test_window_reflectance_averages_only_valid_pixels():
    bands = {"B04": np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype="float32")}
    valid = np.array([[True, True, True], [True, False, True], [True, True, True]], dtype=bool)
    extract = extract_window(
        {"B04": np.pad(bands["B04"], 1)}, np.pad(valid, 1), row=2, col=2
    )
    # The invalid centre (5) is excluded; mean of the other 8 = 40/8 = 5.0
    assert extract.n_valid == 8
    assert window_reflectance(extract, "B04") == pytest.approx(5.0)


def test_window_reflectance_all_invalid_is_nan():
    bands = _bands(3.0)
    valid = np.zeros((10, 10), dtype=bool)
    extract = extract_window(bands, valid, row=5, col=5)
    assert extract.n_valid == 0
    assert np.isnan(window_reflectance(extract, "B04"))


def test_chla_gons_matches_hand_computation():
    # One pixel, worked through the canonical Gons form by hand.
    # p applies ONLY to the trailing bb term; the bb in (0.70 + bb) is first-power.
    rho_665, rho_705, rho_783 = 0.010, 0.012, 0.004
    bb = 1.56 * rho_783 / (0.082 - 0.6 * rho_783)
    p = 1.063
    a_phy = (0.70 + bb) * (rho_705 / rho_665) - 0.40 - bb**p
    expected = a_phy / GONS_ASTAR_PHY_665

    result = chla_gons(np.array([rho_665]), np.array([rho_705]), np.array([rho_783]))
    assert result[0] == pytest.approx(expected)


def test_chla_gons_bb_exponent_only_on_trailing_term():
    # Guard against the earlier bug where p was applied to both bb terms.
    # With p != 1 the two formulations diverge; pin the correct one.
    rho_665, rho_705, rho_783 = 0.010, 0.013, 0.005
    bb = 1.56 * rho_783 / (0.082 - 0.6 * rho_783)
    correct = ((0.70 + bb) * (rho_705 / rho_665) - 0.40 - bb**1.063) / GONS_ASTAR_PHY_665
    buggy = ((0.70 + bb**1.063) * (rho_705 / rho_665) - 0.40 - bb**1.063) / GONS_ASTAR_PHY_665
    result = chla_gons(np.array([rho_665]), np.array([rho_705]), np.array([rho_783]))[0]
    assert result == pytest.approx(correct)
    assert result != pytest.approx(buggy)  # the two really are different


def test_chla_gons_rises_with_red_edge_ratio():
    # Higher rho(705)/rho(665) means more Chl-a — the physical direction.
    rho_665 = np.array([0.010, 0.010])
    rho_705 = np.array([0.011, 0.015])  # second pixel has a stronger red-edge peak
    rho_783 = np.array([0.004, 0.004])
    chla = chla_gons(rho_665, rho_705, rho_783)
    assert chla[1] > chla[0]


def test_chla_gons_is_vectorised_over_a_window():
    rho = {b: np.full((3, 3), v) for b, v in (("665", 0.01), ("705", 0.013), ("783", 0.004))}
    chla = chla_gons(rho["665"], rho["705"], rho["783"])
    assert chla.shape == (3, 3)
    assert np.all(np.isfinite(chla))
