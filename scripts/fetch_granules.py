#!/usr/bin/env python
"""Fetch the Sentinel-2 L1C granules needed for match-ups from Copernicus S3.

Downloads only the distinct scenes that actually participate in a match-up (71 of
1382 indexed at the time of writing), not the whole scene index. Resumable: any
object already present with the right size is skipped, so an interrupted run can
simply be repeated.

Credentials — generate an S3 key pair at
https://eodata-s3keysmanager.dataspace.copernicus.eu/ and export:

    export CDSE_S3_ACCESS_KEY="..."
    export CDSE_S3_SECRET_KEY="..."

AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY are accepted as fallbacks. In CI the
secrets are CDSE_S3_ACCESS_KEY / CDSE_S3_SECRET_KEY.

Usage:
    pixi run python scripts/fetch_granules.py                     # all match-up scenes
    pixi run python scripts/fetch_granules.py --quantity chlorophyll_a
    pixi run python scripts/fetch_granules.py --dry-run           # report size only
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

ENDPOINT = "https://eodata.dataspace.copernicus.eu"
BUCKET = "eodata"

REPO_ROOT = Path(__file__).resolve().parent.parent
MATCHUPS = REPO_ROOT / "data" / "interim" / "matchups_westerschelde.parquet"
GRANULE_DIR = REPO_ROOT / "data" / "raw" / "s2"


def s3_client():
    """Boto3 client against the Copernicus S3 endpoint."""
    import boto3
    from botocore.config import Config

    access_key = os.environ.get("CDSE_S3_ACCESS_KEY") or os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("CDSE_S3_SECRET_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY")
    if not (access_key and secret_key):
        sys.exit(
            "No Copernicus S3 credentials found.\n"
            "Set CDSE_S3_ACCESS_KEY and CDSE_S3_SECRET_KEY (see the module docstring)."
        )

    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4", retries={"max_attempts": 5, "mode": "standard"}),
    )


def scene_prefix(s3path: str) -> str:
    """OData S3Path -> bucket-relative key prefix ('/eodata/Sentinel-2/...' -> 'Sentinel-2/...')."""
    return s3path.lstrip("/").removeprefix(f"{BUCKET}/")


def list_objects(client, prefix: str) -> list[dict]:
    """Every object under a scene prefix (a .SAFE product is a directory of objects)."""
    objects, token = [], None
    while True:
        kwargs = {"Bucket": BUCKET, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        response = client.list_objects_v2(**kwargs)
        objects.extend(response.get("Contents", []))
        if not response.get("IsTruncated"):
            return objects
        token = response.get("NextContinuationToken")


def download_scene(client, s3path: str, name: str, dry_run: bool = False) -> tuple[int, int]:
    """Download one .SAFE product. Returns (bytes fetched, bytes already present)."""
    prefix = scene_prefix(s3path)
    objects = list_objects(client, prefix)
    if not objects:
        print(f"  !! no objects under {prefix} — skipping {name}")
        return 0, 0

    fetched = skipped = 0
    for obj in objects:
        key, size = obj["Key"], obj["Size"]
        target = GRANULE_DIR / key
        if target.exists() and target.stat().st_size == size:
            skipped += size
            continue
        if dry_run:
            fetched += size
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(BUCKET, key, str(target))
        fetched += size
    return fetched, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quantity", help="restrict to scenes matching one quantity")
    parser.add_argument("--dry-run", action="store_true", help="report volume, download nothing")
    args = parser.parse_args()

    if not MATCHUPS.exists():
        sys.exit(f"{MATCHUPS} not found — run notebooks/02_data_clean.py first.")

    matchups = pd.read_parquet(MATCHUPS)
    if args.quantity:
        matchups = matchups[matchups["quantity"] == args.quantity]
    scenes = matchups.drop_duplicates("id")[["id", "name", "s3path"]]
    print(f"{len(scenes)} distinct scene(s) required" + (" [dry run]" if args.dry_run else ""))

    GRANULE_DIR.mkdir(parents=True, exist_ok=True)
    client = s3_client()

    total_fetched = total_skipped = 0
    for position, scene in enumerate(scenes.itertuples(), start=1):
        print(f"[{position:>3}/{len(scenes)}] {scene.name}", flush=True)
        fetched, skipped = download_scene(client, scene.s3path, scene.name, args.dry_run)
        total_fetched += fetched
        total_skipped += skipped

    verb = "would fetch" if args.dry_run else "fetched"
    print(f"\n{verb} {total_fetched / 1e9:.1f} GB; {total_skipped / 1e9:.1f} GB already present")
    print(f"granules under {GRANULE_DIR}")


if __name__ == "__main__":
    main()
