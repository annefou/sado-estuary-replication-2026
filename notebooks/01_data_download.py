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
# # 01 — Data download
#
# Fetches every input the replication needs:
#
# 1. **In situ match-up reference** — Rijkswaterstaat (NL) water-quality samples
#    for six Westerschelde estuary-axis stations, March 2018 – March 2020.
#    Open, no credentials.
# 2. **Sentinel-2 MSI Level-1C** — scenes over the Westerschelde for the same
#    window, from the Copernicus Data Space Ecosystem. **Needs credentials.**
#
# Why the Westerschelde and not the Sado estuary of the original paper: no open
# in situ reference exists for the Sado over this period at all. See
# `nanopubs/drafts/00b_in_situ_source_scan.md` for the full source scan and the
# frozen design decision.
#
# **Credentials (Sentinel-2 only).** Neither is needed by *this* notebook —
# scene discovery below is anonymous. They are needed to download granules.
#
# - **Preferred, S3.** Generate a key pair at
#   <https://eodata-s3keysmanager.dataspace.copernicus.eu/> and export
#   `CDSE_S3_ACCESS_KEY` / `CDSE_S3_SECRET_KEY`. Granules are then fetched by
#   `scripts/fetch_granules.py`, which pulls only the scenes that participate in
#   a match-up. This is the route to use for volume, and it is unaffected by
#   two-factor authentication on the account.
# - **Alternative, password grant.** Export `CDSE_USERNAME` / `CDSE_PASSWORD`
#   for the token exchange at the bottom of this notebook. Fails if the account
#   has 2FA/TOTP enabled.
#
# In CI the secrets are `CDSE_S3_ACCESS_KEY` / `CDSE_S3_SECRET_KEY`.
#
# The Rijkswaterstaat half runs without any credential, so a fresh clone can
# always reproduce the in situ reference even before Copernicus access is set up.

# %%
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

RAW_DIR = Path("../data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# %% [markdown]
# ## Study area and period
#
# The six stations run the estuary axis from Vlissingen at the mouth to Schaar
# van Ouden Doel at the Belgian border, mirroring the inner/outer gradient the
# original study sampled in the Sado. Codes and coordinates come from the
# Rijkswaterstaat catalogue (`OphalenCatalogus`); coordinates are ETRS89.

# %%
# Study period: the full Sentinel-2 era, NOT the original study's March 2018 –
# March 2020 field-campaign window.
#
# Why: at the original window this replication yielded only 13–16 chlorophyll
# match-ups — comparable to the paper's own N = 19–21, not an improvement on it.
# Adding stations does not help, because Rijkswaterstaat samples the whole
# estuary on the same cruise days and every Westerschelde station falls in the
# same two MGRS tiles, so extra stations contribute observations on the *same*
# dates against the *same* scenes. Only more dates help.
#
# The original window was set by the authors' field campaign, not by anything
# about the science, and we already depart from the paper on site — so period
# correspondence was never load-bearing. Extending also makes turbidity
# testable: Rijkswaterstaat turbidity at these stations begins in 2024.
# See nanopubs/drafts/00b_in_situ_source_scan.md.
PERIOD_START = "2016-01-01T00:00:00.000+01:00"
PERIOD_END = "2026-07-23T00:00:00.000+01:00"

# Westerschelde bounding box (lon_min, lat_min, lon_max, lat_max), WGS84.
WESTERSCHELDE_BBOX = (3.35, 51.30, 4.35, 51.58)

STATIONS = {
    "vlissingen.boeissvh": {"name": "Vlissingen, boei SSVH", "lat": 51.411991, "lon": 3.565619},
    "terneuzen.boei20": {"name": "Terneuzen, boei 20", "lat": 51.346500, "lon": 3.825500},
    "hansweert.geul": {"name": "Hansweert, geul", "lat": 51.436114, "lon": 4.014149},
    "lodijksegat": {"name": "Lodijkse Gat", "lat": 51.515300, "lon": 4.127100},
    "soelekerkepolder.oost": {"name": "Soelekerkepolder, oost", "lat": 51.542200, "lon": 3.730800},
    "schaarvanoudendoel": {"name": "Schaar van Ouden Doel", "lat": 51.350292, "lon": 4.250659},
}

# Rijkswaterstaat encodes each quantity as Grootheid + optional Parameter.
# NOTE: suspended matter is parameter `OS` ("Onopgeloste stoffen"), NOT anything
# containing "zwevende stof" — that phrase is reserved for contaminants measured
# *in* the suspended-matter phase. Searching the obvious Dutch term finds nothing
# and wrongly suggests SPM is unavailable.
QUANTITIES = {
    "chlorophyll_a": {"grootheid": "CONCTTE", "parameter": "CHLFa", "unit": "ug/l"},
    "spm": {"grootheid": "CONCTTE", "parameter": "OS", "unit": "mg/l"},
    "turbidity": {"grootheid": "TROEBHD", "parameter": None, "unit": "NTU/FNU"},
    "phaeophytin_a": {"grootheid": "CONCTTE", "parameter": "FEOa", "unit": "ug/l"},
    "secchi_depth": {"grootheid": "ZICHT", "parameter": None, "unit": "dm"},
}

# Turbidity is included now that the period extends past 2024 — it has no records
# at these stations before then. aCDOM has no open equivalent at all and stays
# untested; that must be declared in the Outcome's limitations.

# %% [markdown]
# ## 1. Rijkswaterstaat in situ match-up reference
#
# DDAPI 2.0. The legacy `waterwebservices.rijkswaterstaat.nl` host is being
# decommissioned (end of April 2026) — this uses the current base URL.
# A 204 response means "no observations", not an error.

# %%
RWS_BASE = "https://ddapi20-waterwebservices.rijkswaterstaat.nl"
RWS_OBSERVATIONS = f"{RWS_BASE}/ONLINEWAARNEMINGENSERVICES/OphalenWaarnemingen"


def fetch_rws_series(
    station_code: str, grootheid: str, parameter: str | None, timeout: int = 300
) -> pd.DataFrame:
    """Fetch one quantity at one station over the study period."""
    aquo: dict = {"Compartiment": {"Code": "OW"}, "Grootheid": {"Code": grootheid}}
    if parameter:
        aquo["Parameter"] = {"Code": parameter}

    payload = {
        "Locatie": {"Code": station_code},
        "AquoPlusWaarnemingMetadata": {"AquoMetadata": aquo},
        "Periode": {"Begindatumtijd": PERIOD_START, "Einddatumtijd": PERIOD_END},
    }
    response = requests.post(
        RWS_OBSERVATIONS,
        json=payload,
        headers={"X-API-KEY": "debug"},
        timeout=timeout,
    )
    if response.status_code == 204:  # no observations for this combination
        return pd.DataFrame(
            columns=["station", "time", "value", "unit", "quality_code", "status"]
        )
    response.raise_for_status()

    rows = []
    for block in response.json().get("WaarnemingenLijst") or []:
        unit = (block.get("AquoMetadata", {}).get("Eenheid") or {}).get("Code")
        for measurement in block.get("MetingenLijst", []):
            value = measurement.get("Meetwaarde")
            if isinstance(value, dict):  # API nests the scalar under Waarde_Numeriek
                value = value.get("Waarde_Numeriek")
            observation_meta = measurement.get("WaarnemingMetadata") or {}
            rows.append(
                {
                    "station": station_code,
                    "time": measurement.get("Tijdstip"),
                    "value": value,
                    "unit": unit,
                    "quality_code": observation_meta.get("Kwaliteitswaardecode"),
                    "status": observation_meta.get("Statuswaarde"),
                }
            )
    return pd.DataFrame(rows)


# %%
def fetch_all_rws() -> pd.DataFrame:
    """Fetch every quantity at every station into one tidy long-format frame."""
    frames = []
    for quantity, spec in QUANTITIES.items():
        for code in STATIONS:
            frame = fetch_rws_series(code, spec["grootheid"], spec["parameter"])
            if not frame.empty:
                frame["quantity"] = quantity
                frames.append(frame)
            print(f"  {quantity:<16} {code:<24} n={len(frame)}")
    if not frames:
        raise RuntimeError("Rijkswaterstaat returned no data for any station/quantity.")
    return pd.concat(frames, ignore_index=True)


print("Fetching Rijkswaterstaat in situ observations...")
in_situ = fetch_all_rws()

# %% [markdown]
# ### Screen Rijkswaterstaat's missing-data marker
#
# **This step is load-bearing.** Rijkswaterstaat encodes "no value" as the
# literal number `999999999999`, not as null. It arrives as an ordinary float
# and is invisible to `dropna()`. Left in, it inflates every mean by ~10¹¹ and
# silently destroys the analysis — chlorophyll means came out at 2×10¹¹ µg/l
# before this filter was added.
#
# 152 of 1005 raw observations carry the marker. It is not spread evenly:
# `soelekerkepolder.oost` accounts for 38 of the chlorophyll gaps and 33 of the
# SPM gaps, so that station is roughly half empty and should be treated with
# care when interpreting station-level results.

# %%
RWS_MISSING = 999_999_999_999.0

in_situ["time"] = pd.to_datetime(in_situ["time"], format="ISO8601", utc=True)
in_situ = in_situ.dropna(subset=["value"])

n_raw = len(in_situ)
missing_mask = in_situ["value"] >= RWS_MISSING
print(f"\nScreening {int(missing_mask.sum())} missing-data markers of {n_raw} observations:")
print(
    in_situ[missing_mask].groupby(["quantity", "station"]).size().to_string()
    or "  (none)"
)

in_situ = in_situ[~missing_mask].sort_values(["quantity", "station", "time"])

for name, meta in STATIONS.items():
    in_situ.loc[in_situ["station"] == name, "station_name"] = meta["name"]
    in_situ.loc[in_situ["station"] == name, "lat"] = meta["lat"]
    in_situ.loc[in_situ["station"] == name, "lon"] = meta["lon"]

# Tabular results -> parquet (DOMAIN.md § Data formats; never .npz).
in_situ_path = RAW_DIR / "rws_in_situ_westerschelde.parquet"
in_situ.to_parquet(in_situ_path, index=False)

print(f"\n{len(in_situ)} usable observations -> {in_situ_path}")
print(in_situ.groupby("quantity")["value"].agg(["count", "mean", "min", "max"]).to_string())

# %% [markdown]
# ## 2. Sentinel-2 MSI Level-1C
#
# Copernicus Data Space Ecosystem OData catalogue. Scene *discovery* is
# anonymous; only the download needs a token, so the query below runs and
# reports scene counts even without credentials.
#
# **Processing baseline.** ESA reprocessed the whole archive to baseline 04.00,
# which introduced a radiometric offset in L1C TOA reflectance. Data for
# 2018–2020 therefore arrives on the new baseline today even though it predates
# it. The atmospheric-correction step must be baseline-04.00-aware — this is why
# Polymer is pinned to v4.17.3 and not the paper's v4.12. See
# `docs/polymer-licence-and-version.md`.

# %%
CDSE_ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"


def query_s2_scenes(max_cloud: int = 60) -> pd.DataFrame:
    """List S2 L1C scenes intersecting the Westerschelde over the study period."""
    lon_min, lat_min, lon_max, lat_max = WESTERSCHELDE_BBOX
    polygon = (
        f"POLYGON(({lon_min} {lat_min},{lon_max} {lat_min},"
        f"{lon_max} {lat_max},{lon_min} {lat_max},{lon_min} {lat_min}))"
    )
    filter_expr = (
        "Collection/Name eq 'SENTINEL-2' "
        "and contains(Name,'MSIL1C') "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;{polygon}') "
        f"and ContentDate/Start gt {PERIOD_START[:10]}T00:00:00.000Z "
        f"and ContentDate/Start lt {PERIOD_END[:10]}T00:00:00.000Z "
        "and Attributes/OData.CSC.DoubleAttribute/any(a:a/Name eq 'cloudCover' "
        f"and a/OData.CSC.DoubleAttribute/Value lt {max_cloud})"
    )

    scenes, url = [], None
    params = {
        "$filter": filter_expr,
        "$top": "1000",
        "$orderby": "ContentDate/Start",
        "$expand": "Attributes",
    }
    while True:
        response = requests.get(url or CDSE_ODATA, params=None if url else params, timeout=300)
        response.raise_for_status()
        payload = response.json()
        scenes.extend(payload.get("value", []))
        url = payload.get("@odata.nextLink")
        if not url:
            break

    def cloud_of(scene: dict) -> float | None:
        for attribute in scene.get("Attributes") or []:
            if attribute.get("Name") == "cloudCover":
                return attribute.get("Value")
        return None

    return pd.DataFrame(
        [
            {
                "id": s["Id"],
                "name": s["Name"],
                "start": s["ContentDate"]["Start"],
                # MGRS tile, e.g. T31UES — the Westerschelde spans more than one.
                "tile": next((p for p in s["Name"].split("_") if p.startswith("T") and len(p) == 6), None),
                "cloud_cover": cloud_of(s),
                # GeoJSON polygon: lets 02 test station-in-scene properly rather than
                # assuming every scene intersecting the bbox covers every station.
                "footprint": json.dumps(s.get("GeoFootprint")),
                "s3path": s.get("S3Path"),
            }
            for s in scenes
        ]
    )


# %%
try:
    scenes = query_s2_scenes()
    scenes.to_parquet(RAW_DIR / "s2_l1c_scene_index.parquet", index=False)
    print(f"{len(scenes)} Sentinel-2 L1C scenes over the Westerschelde, {PERIOD_START[:10]}–{PERIOD_END[:10]}")
except requests.RequestException as exc:  # catalogue unreachable -> don't kill the notebook
    scenes = pd.DataFrame()
    print(f"Scene query failed ({exc}). The in situ reference above is unaffected.")

# %% [markdown]
# ### Scene download
#
# Downloading needs a Copernicus token. Without credentials this cell reports
# what it *would* fetch and stops cleanly, so the notebook still executes
# end-to-end on a fresh clone.

# %%
def cdse_token() -> str | None:
    """Exchange CDSE credentials for an access token; None if unset."""
    username, password = os.environ.get("CDSE_USERNAME"), os.environ.get("CDSE_PASSWORD")
    if not (username and password):
        return None
    response = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "username": username,
            "password": password,
            "client_id": "cdse-public",
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["access_token"]


token = cdse_token()
if token is None:
    print(
        f"CDSE credentials not set — skipping download of {len(scenes)} scene(s).\n"
        "Set CDSE_USERNAME and CDSE_PASSWORD to enable. See the header of this notebook."
    )
else:
    print(f"Authenticated to CDSE. {len(scenes)} scene(s) queued for download.")
    # Download implemented in the pipeline run; scenes are large (~700 MB each)
    # and are cached under data/raw/s2/ via actions/cache in CI.

# %% [markdown]
# ## Source registry

# %%
def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


SOURCES = [
    {
        "name": "Rijkswaterstaat water-quality observations, Westerschelde",
        "doi": None,
        "url": RWS_OBSERVATIONS,
        "license": "Open data (Rijkswaterstaat / CC0-equivalent public task data)",
        "accessed_on": datetime.now(timezone.utc).date().isoformat(),
        "sha256": sha256sum(in_situ_path),
        "notes": (
            f"{len(in_situ)} observations, {len(STATIONS)} stations, "
            f"{PERIOD_START[:10]} to {PERIOD_END[:10]}. "
            "Quantities: chlorophyll-a, SPM (parameter OS), phaeophytin-a, Secchi depth. "
            "Turbidity and aCDOM verified absent for this period."
        ),
    },
    {
        "name": "Sentinel-2 MSI Level-1C",
        "doi": None,
        "url": CDSE_ODATA,
        "license": "Copernicus Open Data (free, full and open)",
        "accessed_on": datetime.now(timezone.utc).date().isoformat(),
        "sha256": None,  # per-scene checksums recorded at download time
        "notes": (
            f"{len(scenes)} scenes intersecting {WESTERSCHELDE_BBOX}. "
            "Archive reprocessed to processing baseline 04.00 (TOA reflectance offset)."
        ),
    },
]

with open(RAW_DIR / "sources.json", "w") as f:
    json.dump({"sources": SOURCES}, f, indent=2)

print(f"Logged {len(SOURCES)} source(s) to {RAW_DIR / 'sources.json'}")
