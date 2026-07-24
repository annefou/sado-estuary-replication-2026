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
# # 02 — Data clean: match-up construction
#
# Pairs each in situ observation with the Sentinel-2 scenes that could validate
# it, following the original study's match-up protocol:
#
# | Criterion | Sent et al. (2021) | Here |
# |---|---|---|
# | Time window | ±2 h | ±2 h (unchanged) |
# | Spatial window | 3×3 pixels at 10 m | 3×3 pixels at 10 m (unchanged) |
# | Cloud screening | IdePix v2.2 + processor flags | applied in `03_analysis.py`, per-pixel |
# | Scene cloud cover | not stated | < 60 % scene-level pre-filter (in `01`) |
#
# This notebook resolves the **temporal and geometric** half of the match-up:
# which (observation, scene) pairs exist at all. Per-pixel quality screening
# needs the granule rasters and happens in `03_analysis.py`, so the counts here
# are an **upper bound** on the final N.
#
# The whole notebook runs from the two parquet files written by `01`, with no
# credentials and no scene downloads.

# %%
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from shapely.geometry import Point, shape

RAW_DIR = Path("../data/raw")
INTERIM_DIR = Path("../data/interim")
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

MATCHUP_WINDOW = pd.Timedelta(hours=2)

# %%
in_situ = pd.read_parquet(RAW_DIR / "rws_in_situ_westerschelde.parquet")
scenes = pd.read_parquet(RAW_DIR / "s2_l1c_scene_index.parquet")

scenes["start"] = pd.to_datetime(scenes["start"], format="ISO8601", utc=True)
scenes["geometry"] = scenes["footprint"].map(lambda f: shape(json.loads(f)) if f else None)
scenes = scenes.dropna(subset=["geometry"])

print(f"{len(in_situ)} in situ observations, {len(scenes)} candidate scenes")
print(f"scene tiles: {sorted(scenes['tile'].dropna().unique())}")

# %% [markdown]
# ## Which scenes actually cover which stations?
#
# A scene intersecting the estuary bounding box does not necessarily contain a
# given station — the Westerschelde straddles more than one MGRS tile, so this
# has to be tested per station rather than assumed.

# %%
stations = (
    in_situ[["station", "station_name", "lat", "lon"]]
    .drop_duplicates()
    .reset_index(drop=True)
)
stations["point"] = stations.apply(lambda r: Point(r["lon"], r["lat"]), axis=1)

coverage = {
    row.station: scenes["geometry"].map(lambda g: g.covers(row.point)).values
    for row in stations.itertuples()
}
for station, mask in coverage.items():
    name = stations.loc[stations["station"] == station, "station_name"].iloc[0]
    print(f"  {name:<26} covered by {int(mask.sum()):>3} / {len(scenes)} scenes")

# %% [markdown]
# ## Temporal pairing (±2 h)

# %%
def match_station(station_code: str) -> pd.DataFrame:
    """Pair every observation at one station with scenes inside the ±2 h window."""
    observations = in_situ[in_situ["station"] == station_code]
    covering = scenes[coverage[station_code]]
    if observations.empty or covering.empty:
        return pd.DataFrame()

    pairs = observations.merge(covering, how="cross", suffixes=("", "_scene"))
    pairs["dt"] = (pairs["start"] - pairs["time"]).abs()
    return pairs[pairs["dt"] <= MATCHUP_WINDOW]


matchups = pd.concat(
    [match_station(code) for code in stations["station"]], ignore_index=True
)

# %%
if matchups.empty:
    raise RuntimeError("No match-ups found — check the window or the scene index.")

matchups = matchups[
    [
        "station", "station_name", "lat", "lon", "quantity", "value", "unit",
        "time", "id", "name", "tile", "cloud_cover", "start", "dt", "s3path",
    ]
].sort_values(["quantity", "station", "time"])

out_path = INTERIM_DIR / "matchups_westerschelde.parquet"
matchups.to_parquet(out_path, index=False)

print(f"{len(matchups)} (observation, scene) pairs -> {out_path}\n")
print("Pairs per quantity:")
print(matchups.groupby("quantity").size().to_string())

# %% [markdown]
# ## How many *observations* are validated, not how many pairs
#
# One observation can pair with more than one scene (adjacent tiles imaged in
# the same overpass). The number that matters for statistical power is the count
# of distinct observations with at least one scene — that is the analogue of the
# original study's N = 19–21.

# %%
per_observation = (
    matchups.groupby(["quantity", "station", "time"]).size().rename("n_scenes").reset_index()
)
summary = (
    per_observation.groupby("quantity")
    .agg(observations_matched=("n_scenes", "size"), scene_pairs=("n_scenes", "sum"))
    .join(in_situ.groupby("quantity").size().rename("observations_total"))
)
summary["match_rate"] = (
    summary["observations_matched"] / summary["observations_total"]
).map("{:.1%}".format)

print(summary.to_string())

# %%
print("\nMatched observations per station (chlorophyll-a):")
chl = per_observation[per_observation["quantity"] == "chlorophyll_a"]
print(chl.groupby("station").size().to_string())

print("\nCloud cover of matched scenes (%):")
print(matchups["cloud_cover"].describe()[["count", "mean", "min", "max"]].to_string())

# %% [markdown]
# ## Caveat on these counts
#
# These are an **upper bound**. Every pair still has to survive, in `03`:
#
# - per-pixel cloud, cloud-shadow and glint flagging over the 3×3 window;
# - the requirement that the 3×3 window is entirely water (several stations sit
#   close to channel edges and intertidal flats);
# - atmospheric-correction failure flags, which differ per processor and are
#   themselves part of what the original study compared.
#
# Do not quote the numbers above as the replication's N. The realised N goes in
# `05_outcome.md` and comes from `03_analysis.py`.

# %%
summary.to_csv(INTERIM_DIR / "matchup_summary.csv")
print(f"\nWrote {INTERIM_DIR / 'matchup_summary.csv'}")
