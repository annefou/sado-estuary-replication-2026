"""Agreement statistics for satellite / in situ match-ups.

Reproduces the metric suite of Sent et al. (2021) Table 4 — R², slope, intercept,
RMSE, BIAS, URMS, APD, RPD — so the replication's numbers are directly comparable
in *form* to the original's, even though site and period differ.

One detail from the paper's methods matters and is easy to get wrong:
**chlorophyll-a statistics are computed in log space, but APD and RPD are not
log-transformed.** Mixing that up changes the reported numbers substantially,
because Chl-a spans orders of magnitude. `matchup_statistics(..., log=True)`
implements exactly that split.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class MatchupStats:
    """Agreement metrics for one satellite/in-situ pair set."""

    n: int
    r2: float
    slope: float
    intercept: float
    rmse: float
    bias: float
    urms: float
    apd: float
    rpd: float
    log_space: bool

    def as_dict(self) -> dict:
        return asdict(self)


def _finite_pairs(satellite: np.ndarray, in_situ: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Drop pairs where either side is missing or non-positive."""
    satellite = np.asarray(satellite, dtype="float64")
    in_situ = np.asarray(in_situ, dtype="float64")
    if satellite.shape != in_situ.shape:
        raise ValueError(f"shape mismatch: {satellite.shape} vs {in_situ.shape}")
    keep = np.isfinite(satellite) & np.isfinite(in_situ) & (satellite > 0) & (in_situ > 0)
    return satellite[keep], in_situ[keep]


def matchup_statistics(
    satellite: np.ndarray, in_situ: np.ndarray, *, log: bool = False
) -> MatchupStats:
    """Agreement metrics. With log=True, regression metrics use log10; APD/RPD do not.

    Non-positive values are dropped: they are physically invalid for the
    quantities here and undefined in log space. Dropping them is a real filter —
    report how many were removed alongside the statistics.
    """
    satellite, in_situ = _finite_pairs(satellite, in_situ)
    n = satellite.size
    if n < 3:
        raise ValueError(f"need at least 3 valid pairs, got {n}")

    # Regression-family metrics, optionally in log space (the paper's Chl-a convention).
    x = np.log10(in_situ) if log else in_situ
    y = np.log10(satellite) if log else satellite

    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept
    ss_residual = float(np.sum((y - predicted) ** 2))
    ss_total = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_residual / ss_total if ss_total > 0 else float("nan")

    difference = y - x
    bias = float(difference.mean())
    rmse = float(np.sqrt(np.mean(difference**2)))
    # Unbiased RMS: the scatter that remains once the mean offset is removed.
    urms = float(np.sqrt(np.mean((difference - bias) ** 2)))

    # APD / RPD always on untransformed values — explicitly per the paper's methods.
    relative = (satellite - in_situ) / in_situ
    apd = float(np.mean(np.abs(relative)) * 100.0)
    rpd = float(np.mean(relative) * 100.0)

    return MatchupStats(
        n=n,
        r2=float(r2),
        slope=float(slope),
        intercept=float(intercept),
        rmse=rmse,
        bias=bias,
        urms=urms,
        apd=apd,
        rpd=rpd,
        log_space=log,
    )


def stratified_statistics(
    satellite: np.ndarray,
    in_situ: np.ndarray,
    times: np.ndarray,
    *,
    log: bool = False,
    subset: tuple[str, str] = ("2018-03-01", "2020-04-01"),
) -> dict[str, MatchupStats]:
    """Statistics over the full record and over the original study's window.

    Reporting both partially separates the *site* effect from the *period*
    effect: this replication changed both, and neither number alone can tell
    them apart. The subset will be underpowered — say so when reporting it.
    """
    times = np.asarray(times, dtype="datetime64[ns]")
    start, end = (np.datetime64(bound) for bound in subset)
    in_window = (times >= start) & (times < end)

    results = {"full_record": matchup_statistics(satellite, in_situ, log=log)}
    if in_window.sum() >= 3:
        results["original_window"] = matchup_statistics(
            satellite[in_window], in_situ[in_window], log=log
        )
    return results
