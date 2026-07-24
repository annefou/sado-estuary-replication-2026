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
# # 04 — Figures: the Chl-a validation result
#
# The headline figure is a **match-up agreement plot** — satellite-derived
# chlorophyll-a (Acolite + Gons, the `aGS` chain) against the coincident
# Rijkswaterstaat in situ Chl-a, on log–log axes with the 1:1 line. This is the
# standard form for ocean-colour validation and mirrors the original paper's
# Table 4 comparison; it is the figure the whole replication turns on.
#
# Two point sets are shown: the full 2016–2026 record and the 2018–2020 subset
# matching the original study's window (the site/period-confound mitigation from
# `nanopubs/drafts/00b_in_situ_source_scan.md`). Agreement statistics come from
# the tested `scripts/matchup_stats.py`, computed **in log space** as the paper
# did for Chl-a.
#
# **Inline display rule:** always pair `fig.savefig(...)` with `plt.show()` — MyST
# builds an empty cell otherwise. No `matplotlib.use('Agg')`.

# %%
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("../scripts").resolve()))
from matchup_stats import matchup_statistics

plt.style.use("seaborn-v0_8-whitegrid")  # USER_PREFERENCES

RAW_DIR = Path("../data/raw")
RESULTS_DIR = Path("../results")
FIGURES_DIR = Path("../figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Okabe–Ito — a published colour-blind-safe qualitative palette. Two entities:
# the full record and the original-window subset. Colour follows the entity.
COLOUR_FULL = "#0072B2"  # blue
COLOUR_SUBSET = "#E69F00"  # orange
ORIGINAL_WINDOW = ("2018-03-01", "2020-04-01")

# The original study's selected Chl-a chain (cGS = C2RCC + Gons), for reference —
# from Sent et al. (2021) Table 4 / § 3.2. See nanopubs/drafts/00_paper_summary.md.
PAPER_CGS_R2 = 0.63

# %% [markdown]
# ## Build the match-up pairs
#
# `03` writes one satellite Chl-a per (station, in situ sample time); joining to
# the in situ table on those keys pairs each retrieval with its ground truth.

# %%
def load_matchup_pairs() -> pd.DataFrame:
    """Pair satellite (aGS) Chl-a with coincident in situ Chl-a."""
    satellite = pd.read_parquet(RESULTS_DIR / "chla_satellite_acolite.parquet")
    in_situ = pd.read_parquet(RAW_DIR / "rws_in_situ_westerschelde.parquet")
    in_situ = in_situ[in_situ["quantity"] == "chlorophyll_a"][["station", "time", "value"]]
    in_situ = in_situ.rename(columns={"value": "chla_in_situ"})

    pairs = satellite.merge(in_situ, on=["station", "time"], how="inner")
    pairs = pairs.dropna(subset=["chla_satellite", "chla_in_situ"])
    return pairs[pairs["chla_satellite"] > 0]


pairs = load_matchup_pairs()
pairs["time"] = pd.to_datetime(pairs["time"], utc=True)
start, end = (pd.Timestamp(b, tz="UTC") for b in ORIGINAL_WINDOW)
pairs["in_window"] = (pairs["time"] >= start) & (pairs["time"] < end)
print(f"{len(pairs)} match-up pairs ({int(pairs['in_window'].sum())} in the 2018–2020 window)")

# %% [markdown]
# ## The validation figure

# %%
def agreement_lines(pairs: pd.DataFrame) -> dict:
    """Log-space agreement stats for the full record and the original window."""
    out = {}
    full = matchup_statistics(pairs["chla_satellite"].to_numpy(), pairs["chla_in_situ"].to_numpy(), log=True)
    out["full"] = full
    subset = pairs[pairs["in_window"]]
    if len(subset) >= 3:
        out["subset"] = matchup_statistics(
            subset["chla_satellite"].to_numpy(), subset["chla_in_situ"].to_numpy(), log=True
        )
    return out


def annotate(stats, colour: str, y0: float, label: str, ax) -> None:
    box = (
        f"{label}: N={stats.n}, R²={stats.r2:.2f}, "
        f"slope={stats.slope:.2f}, RMSE={stats.rmse:.2f} (log₁₀)"
    )
    ax.text(0.03, y0, box, transform=ax.transAxes, color=colour, fontsize=9, va="top")


stats = agreement_lines(pairs)

fig, ax = plt.subplots(figsize=(6, 6))

# 1:1 line across the shared data range.
lo = float(min(pairs["chla_in_situ"].min(), pairs["chla_satellite"].min())) * 0.7
hi = float(max(pairs["chla_in_situ"].max(), pairs["chla_satellite"].max())) * 1.3
ax.plot([lo, hi], [lo, hi], color="0.4", lw=1, ls="--", zorder=1, label="1:1")

full_pts = pairs[~pairs["in_window"]]
sub_pts = pairs[pairs["in_window"]]
ax.scatter(
    full_pts["chla_in_situ"], full_pts["chla_satellite"],
    s=28, c=COLOUR_FULL, alpha=0.75, edgecolor="white", linewidth=0.5,
    label="2016–2026", zorder=3,
)
ax.scatter(
    sub_pts["chla_in_situ"], sub_pts["chla_satellite"],
    s=34, c=COLOUR_SUBSET, alpha=0.9, edgecolor="white", linewidth=0.5,
    label="2018–2020 (original window)", zorder=4,
)

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(lo, hi)
ax.set_ylim(lo, hi)
ax.set_aspect("equal")
ax.set_xlabel("In situ chlorophyll-a  (µg L⁻¹)")
ax.set_ylabel("Satellite chlorophyll-a, Acolite + Gons  (µg L⁻¹)")
ax.set_title("Sentinel-2 MSI Chl-a retrieval vs in situ, Westerschelde")

annotate(stats["full"], COLOUR_FULL, 0.97, "Full record", ax)
if "subset" in stats:
    annotate(stats["subset"], COLOUR_SUBSET, 0.90, "Original window", ax)
ax.text(
    0.03, 0.83, f"Original study (cGS): R²={PAPER_CGS_R2:.2f}",
    transform=ax.transAxes, color="0.35", fontsize=9, va="top", style="italic",
)
ax.legend(loc="lower right", frameon=True, framealpha=0.9)

fig.tight_layout()
fig.savefig(FIGURES_DIR / "main_result.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES_DIR / "main_result.pdf", bbox_inches="tight")  # publication vector
plt.show()  # required for MyST inline display

# %% [markdown]
# ## How to read it
#
# Points on the 1:1 line are perfect agreement; systematic offset from it is bias,
# scatter around it is random error. Compare the full-record and original-window R²
# with the original study's cGS R² = 0.63 — but characterise the result honestly
# (`docs/claim-type-vocabulary.md`): a different estuary is a different optical
# regime, so a divergence speaks to *generalisability*, not to whether the original
# analysis was correct (`nanopubs/drafts/00b_in_situ_source_scan.md`).
