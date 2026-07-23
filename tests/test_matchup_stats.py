"""Tests for the match-up agreement statistics.

These pin behaviour that is easy to get silently wrong: the log/linear split
between regression metrics and APD/RPD, sign conventions on BIAS and RPD, and
the RMSE² = BIAS² + URMS² identity.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from matchup_stats import matchup_statistics, stratified_statistics  # noqa: E402


def test_perfect_agreement_is_exact():
    values = np.array([1.0, 2.0, 5.0, 10.0, 20.0])
    stats = matchup_statistics(values, values)
    assert stats.n == 5
    assert stats.r2 == pytest.approx(1.0)
    assert stats.slope == pytest.approx(1.0)
    assert stats.intercept == pytest.approx(0.0, abs=1e-12)
    assert stats.rmse == pytest.approx(0.0, abs=1e-12)
    assert stats.bias == pytest.approx(0.0, abs=1e-12)
    assert stats.apd == pytest.approx(0.0, abs=1e-12)
    assert stats.rpd == pytest.approx(0.0, abs=1e-12)


def test_bias_and_rpd_signs_follow_satellite_minus_in_situ():
    in_situ = np.array([1.0, 2.0, 4.0, 8.0])
    satellite = in_situ * 1.5  # satellite reads high
    stats = matchup_statistics(satellite, in_situ)
    assert stats.bias > 0
    assert stats.rpd == pytest.approx(50.0)
    assert stats.apd == pytest.approx(50.0)


def test_apd_and_rpd_diverge_when_errors_cancel():
    in_situ = np.array([10.0, 10.0, 10.0, 10.0])
    satellite = np.array([12.0, 8.0, 12.0, 8.0])  # +20%, -20% alternating
    stats = matchup_statistics(satellite, in_situ)
    assert stats.rpd == pytest.approx(0.0, abs=1e-12)  # cancels
    assert stats.apd == pytest.approx(20.0)  # does not


def test_rmse_decomposes_into_bias_and_urms():
    rng = np.random.default_rng(20260723)
    in_situ = rng.uniform(1.0, 50.0, size=200)
    satellite = in_situ * 1.2 + rng.normal(0.0, 2.0, size=200)
    stats = matchup_statistics(satellite, in_situ)
    assert stats.rmse**2 == pytest.approx(stats.bias**2 + stats.urms**2, rel=1e-9)


def test_log_flag_changes_regression_metrics_but_not_apd():
    rng = np.random.default_rng(7)
    in_situ = 10 ** rng.uniform(-1, 2, size=100)  # spans orders of magnitude
    satellite = in_situ * rng.lognormal(0.0, 0.3, size=100)

    linear = matchup_statistics(satellite, in_situ, log=False)
    logged = matchup_statistics(satellite, in_situ, log=True)

    assert logged.log_space is True
    assert linear.r2 != pytest.approx(logged.r2)
    assert linear.rmse != pytest.approx(logged.rmse)
    # APD and RPD are defined on untransformed values in both cases.
    assert linear.apd == pytest.approx(logged.apd)
    assert linear.rpd == pytest.approx(logged.rpd)


def test_non_positive_and_missing_pairs_are_dropped():
    in_situ = np.array([1.0, 2.0, -1.0, 4.0, np.nan, 6.0])
    satellite = np.array([1.1, 2.2, 3.0, 0.0, 5.0, 6.6])
    stats = matchup_statistics(satellite, in_situ)
    assert stats.n == 3  # pairs 0, 1, 5 survive


def test_too_few_pairs_raises_rather_than_returning_nonsense():
    with pytest.raises(ValueError, match="at least 3"):
        matchup_statistics(np.array([1.0, 2.0]), np.array([1.0, 2.0]))


def test_shape_mismatch_raises():
    with pytest.raises(ValueError, match="shape mismatch"):
        matchup_statistics(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]))


def test_stratified_splits_out_the_original_window():
    times = np.array(
        ["2017-01-01", "2019-01-01", "2019-06-01", "2019-09-01", "2022-01-01"],
        dtype="datetime64[ns]",
    )
    in_situ = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    satellite = in_situ * 1.1

    results = stratified_statistics(satellite, in_situ, times)
    assert results["full_record"].n == 5
    assert results["original_window"].n == 3  # only the three 2019 points


def test_stratified_omits_window_when_too_few_points():
    times = np.array(["2016-01-01", "2017-01-01", "2022-01-01"], dtype="datetime64[ns]")
    values = np.array([1.0, 2.0, 3.0])
    results = stratified_statistics(values, values, times)
    assert "original_window" not in results
