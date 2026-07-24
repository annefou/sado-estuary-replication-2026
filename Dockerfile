# Replication container: Sentinel-2 water-quality retrieval, Westerschelde.
#
# Atmospheric correction is done by Acolite (GPL-3.0), a pure-Python program
# cloned in stage 1 and run on the pixi environment. That is the whole external
# toolchain — the image is otherwise the pinned pixi env.
#
# Why no SNAP / C2RCC: the original study's selected chain used C2RCC, which
# exists ONLY inside ESA SNAP (a ~2 GB Java application). Four probe iterations
# established that C2RCC segfaults natively in-container even on its required
# Java 11 (crash in libc.so.6), a known SNAP-in-Docker problem. C2RCC is
# therefore excluded and this replication uses the two Python-native processors
# the paper also evaluated — Acolite (here) and Polymer (opt-in). Dropping SNAP
# makes the image dramatically lighter and fully reproducible. The exclusion is a
# declared methodological deviation — see docs/atmospheric-correction-choice.md.
#
# Polymer is deliberately NOT installed: its licence forbids redistribution, so
# it stays an opt-in pixi feature each user installs from Hygeos themselves
# (docs/polymer-licence-and-version.md). This image is therefore safe to make
# public and reproduces the headline Acolite + Gons Chl-a analysis turnkey.

# --------------------------------------------------------------------------- #
# Stage 1 — fetch Acolite (git history dropped so it does not bloat the image)
# --------------------------------------------------------------------------- #
FROM debian:bookworm-slim AS externals

ARG ACOLITE_VERSION=20260421.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${ACOLITE_VERSION}" \
      https://github.com/acolite/acolite.git /opt/acolite \
    && rm -rf /opt/acolite/.git

# --------------------------------------------------------------------------- #
# Stage 2 — runtime
# --------------------------------------------------------------------------- #
FROM ghcr.io/prefix-dev/pixi:0.68.1

LABEL org.opencontainers.image.source="https://github.com/annefou/sado-estuary-replication-2026"
LABEL org.opencontainers.image.description="Replication container: Sentinel-2 water-quality retrieval, Westerschelde. Pure-Python (Acolite); excludes C2RCC/SNAP (native crash) and Polymer (licence)."
LABEL org.opencontainers.image.licenses="MIT AND GPL-3.0"

COPY --from=externals /opt/acolite /opt/acolite

# An `acolite` shim on PATH so notebook 03's subprocess calls resolve without
# knowing the install location. It runs on the pixi environment, which carries
# Acolite's full dependency set (see pixi.toml).
RUN printf '#!/bin/sh\nexec pixi run --manifest-path /app/pixi.toml python /opt/acolite/launch_acolite.py "$@"\n' \
      > /usr/local/bin/acolite && chmod +x /usr/local/bin/acolite

WORKDIR /app

# Install the pinned environment first so the lock layer caches across source edits.
COPY pixi.toml pixi.lock /app/
RUN pixi install --locked

COPY . /app

# Credentials are mounted at runtime, never baked in:
#   docker run -v ~/.aws/credentials:/root/.aws/credentials:ro <image>
# See scripts/fetch_granules.py and docs.

CMD ["pixi", "run", "snakemake", "--cores", "1"]
