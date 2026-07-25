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

# %% [markdown]
# # The asymmetry figure — turbidity vs SPM vs Chl-a
#
# The paper's real headline is not "Chl-a fails" but the **parameter-dependent
# asymmetry**: Sentinel-2 MSI retrieves turbidity strongly, SPM moderately, and
# chlorophyll-a weakly. This panel tests all three limbs with open-source chains
# (Acolite + Nechad for turbidity/SPM, Acolite + Gons for Chl-a) against the same
# Rijkswaterstaat in situ record, and lines each up against the original study's
# selected `c*` chain. Turbidity and SPM are scored in **linear** space, Chl-a in
# **log** space — the paper's conventions (`scripts/matchup_stats.py`).
#
# Units line up without conversion: turbidity FNU↔FNU, SPM mg L⁻¹ ↔ g m⁻³ (equal),
# Chl-a µg L⁻¹ ↔ µg L⁻¹.

# %%
# Left→right = strong→weak, so the asymmetry reads off the page. `paper_r2` is the
# original study's selected-chain R² (Table 4 / § 3.2); `satcol` is the satellite
# value column each 03 parquet uses.
PARAMS = [
    {"key": "turbidity", "label": "Turbidity", "unit": "FNU",
     "sat": "turbidity_satellite_acolite.parquet", "satcol": "value_satellite",
     "log": False, "paper_r2": 0.84, "paper_chain": "cN783", "our_chain": "aN783"},
    {"key": "spm", "label": "SPM", "unit": "mg L⁻¹",
     "sat": "spm_satellite_acolite.parquet", "satcol": "value_satellite",
     "log": False, "paper_r2": 0.49, "paper_chain": "cN740", "our_chain": "aN740"},
    {"key": "chlorophyll_a", "label": "Chlorophyll-a", "unit": "µg L⁻¹",
     "sat": "chla_satellite_acolite.parquet", "satcol": "chla_satellite",
     "log": True, "paper_r2": 0.63, "paper_chain": "cGS", "our_chain": "aGS"},
]


def load_param_pairs(param: dict) -> pd.DataFrame | None:
    """Pair one parameter's satellite retrievals with coincident in situ values.

    Returns None if 03 has not yet written this parameter's parquet, so the figure
    degrades gracefully while the run is still in progress.
    """
    sat_path = RESULTS_DIR / param["sat"]
    if not sat_path.exists():
        return None
    sat = pd.read_parquet(sat_path)
    if sat.empty:
        return None
    in_situ = pd.read_parquet(RAW_DIR / "rws_in_situ_westerschelde.parquet")
    in_situ = in_situ[in_situ["quantity"] == param["key"]][["station", "time", "value"]]
    in_situ = in_situ.rename(columns={"value": "in_situ"})
    sat = sat.rename(columns={param["satcol"]: "sat"})
    pairs = sat.merge(in_situ, on=["station", "time"], how="inner")
    pairs = pairs.dropna(subset=["sat", "in_situ"])
    return pairs[(pairs["sat"] > 0) & (pairs["in_situ"] > 0)]


def draw_panel(ax, param: dict, pairs: pd.DataFrame) -> "MatchupStats | None":
    """One match-up panel with the 1:1 line, in the parameter's native scale."""
    lo = float(min(pairs["in_situ"].min(), pairs["sat"].min())) * 0.7
    hi = float(max(pairs["in_situ"].max(), pairs["sat"].max())) * 1.3
    ax.plot([lo, hi], [lo, hi], color="0.4", lw=1, ls="--", zorder=1)
    ax.scatter(pairs["in_situ"], pairs["sat"], s=26, c=COLOUR_FULL, alpha=0.75,
               edgecolor="white", linewidth=0.5, zorder=3)
    if param["log"]:
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal")
    ax.set_xlabel(f"In situ ({param['unit']})")
    ax.set_ylabel(f"Satellite, {param['our_chain']} ({param['unit']})")

    stats = None
    if len(pairs) >= 3:
        stats = matchup_statistics(pairs["sat"].to_numpy(), pairs["in_situ"].to_numpy(),
                                   log=param["log"])
        space = "log₁₀" if param["log"] else "linear"
        ax.set_title(f"{param['label']}\nN={stats.n}, R²={stats.r2:.2f} ({space})", fontsize=11)
    else:
        ax.set_title(f"{param['label']}\n(insufficient pairs yet)", fontsize=11)
    ax.text(0.04, 0.96, f"orig. {param['paper_chain']}: R²={param['paper_r2']:.2f}",
            transform=ax.transAxes, color="0.35", fontsize=8.5, va="top", style="italic")
    return stats


panels = [(p, load_param_pairs(p)) for p in PARAMS]
available = [(p, pr) for p, pr in panels if pr is not None and len(pr) >= 3]

if available:
    fig, axes = plt.subplots(1, len(available), figsize=(5.2 * len(available), 5.2))
    if len(available) == 1:
        axes = [axes]
    summary = []
    for ax, (param, pairs) in zip(axes, available):
        stats = draw_panel(ax, param, pairs)
        if stats is not None:
            summary.append((param, stats))
    fig.suptitle("Parameter-dependent retrieval accuracy in the Westerschelde "
                 "(open-source chains) vs the original study", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "asymmetry.png", dpi=150, bbox_inches="tight")
    fig.savefig(FIGURES_DIR / "asymmetry.pdf", bbox_inches="tight")
    plt.show()  # required for MyST inline display

    # Comparison table: our open-source chain vs the original's selected chain.
    print(f"\n{'Parameter':14s} {'chain':6s} {'N':>4s} {'R²(ours)':>9s} "
          f"{'R²(orig)':>9s} {'slope':>7s} {'RMSE':>7s} {'BIAS':>7s}")
    for param, s in summary:
        print(f"{param['label']:14s} {param['our_chain']:6s} {s.n:4d} {s.r2:9.2f} "
              f"{param['paper_r2']:9.2f} {s.slope:7.2f} {s.rmse:7.2f} {s.bias:7.2f}")
else:
    print("No parameter parquets available yet — run 03 first (results/*_satellite_acolite.parquet).")

# %% [markdown]
# ## Reading the asymmetry
#
# If the open-source chains reproduce the original's *ordering* — turbidity best,
# Chl-a worst — then the replication supports the paper's central asymmetry claim
# even where absolute agreement differs (different estuary, different processor).
# The turbidity panel is the strong-limb test; the Chl-a panel is the weak-limb
# test drafted in `nanopubs/drafts/05_outcome.md`. Characterise honestly: a strong
# turbidity result *confirms* the paper's confident limb, while the weak Chl-a
# result *qualifies* its cautious limb — together they replicate the asymmetry
# itself, which is the paper's real headline (`nanopubs/drafts/00_paper_summary.md`).
