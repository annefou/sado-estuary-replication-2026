# Replication container. Bundles the full pipeline INCLUDING the atmospheric-
# correction processors, which are external programs rather than conda packages:
#
#   Acolite  (GPL-3.0)  — cloned from github.com/acolite/acolite
#   C2RCC    (GPL-3.0)  — ships inside ESA SNAP, invoked via `gpt`
#
# Polymer is deliberately NOT installed here: its licence forbids redistribution,
# so it stays an opt-in pixi feature each user installs from Hygeos themselves.
# See docs/polymer-licence-and-version.md. This image is therefore safe to make
# public, and reproduces the headline Chl-a analysis (C2RCC + Gons) turnkey.
#
# Multi-stage so the SNAP installer and the Acolite git history do not bloat the
# final image.

# --------------------------------------------------------------------------- #
# Stage 1 — fetch SNAP and Acolite
# --------------------------------------------------------------------------- #
FROM debian:bookworm-slim AS externals

ARG SNAP_VERSION=11
ARG ACOLITE_VERSION=20260421.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates git && rm -rf /var/lib/apt/lists/*

# ESA SNAP — headless install via the official installer's unattended mode.
# The installer is ~1 GB; only the installed tree is carried to the final stage.
RUN wget -q -O /tmp/snap.sh \
      "https://download.esa.int/step/snap/${SNAP_VERSION}.0/installers/esa-snap_all_linux-${SNAP_VERSION}.0.0.sh" \
    && sh /tmp/snap.sh -q -dir /opt/snap \
    && rm /tmp/snap.sh

# Acolite — GPL-3.0, pinned tag, git history dropped.
RUN git clone --depth 1 --branch "${ACOLITE_VERSION}" \
      https://github.com/acolite/acolite.git /opt/acolite \
    && rm -rf /opt/acolite/.git

# --------------------------------------------------------------------------- #
# Stage 2 — runtime
# --------------------------------------------------------------------------- #
FROM ghcr.io/prefix-dev/pixi:0.68.1

LABEL org.opencontainers.image.source="https://github.com/annefou/sado-estuary-replication-2026"
LABEL org.opencontainers.image.description="Replication container: Sentinel-2 water-quality retrieval, Westerschelde. Includes Acolite + SNAP/C2RCC; excludes Polymer (licence)."
LABEL org.opencontainers.image.licenses="MIT AND GPL-3.0"

# SNAP needs a JRE at runtime; Acolite runs on the pixi Python environment.
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless && rm -rf /var/lib/apt/lists/*

COPY --from=externals /opt/snap /opt/snap
COPY --from=externals /opt/acolite /opt/acolite

# Put SNAP's gpt and an `acolite` shim on PATH so notebook 03's subprocess calls
# resolve without knowing install locations.
ENV PATH="/opt/snap/bin:${PATH}"
RUN printf '#!/bin/sh\nexec pixi run --manifest-path /app/pixi.toml python /opt/acolite/launch_acolite.py "$@"\n' \
      > /usr/local/bin/acolite && chmod +x /usr/local/bin/acolite

WORKDIR /app

# Install the pinned environment first so the lock layer caches across source edits.
COPY pixi.toml pixi.lock /app/
RUN pixi install --locked

COPY . /app

# Cap the JVM heap. 6G on a 7G CI runner left no room for SNAP's native
# allocations and the tile cache, which segfaulted C2RCC; 4G is safer. Real
# full-scene runs on a larger host can raise this at run time via `gpt -c`.
RUN sed -i 's/^-Xmx.*/-Xmx4G/' /opt/snap/bin/gpt.vmoptions || true

# Pin SNAP to its BUNDLED JRE (Java 11). The probe showed gpt was picking up the
# system OpenJDK 21 (JAVA_HOME empty), and SNAP 11 on Java 21 is a known JVM
# crash — the likely cause of the C2RCC segfault. `jdkhome` in snap.conf is the
# canonical way to fix SNAP's Java. Belt-and-braces: also export JAVA_HOME.
RUN JRE=$(ls -d /opt/snap/jre 2>/dev/null || ls -d /opt/snap/jdk 2>/dev/null) && \
    echo "jdkhome=\"$JRE\"" >> /opt/snap/etc/snap.conf && \
    echo "Pinned SNAP jdkhome=$JRE"
ENV JAVA_HOME="/opt/snap/jre"

# Credentials are mounted at runtime, never baked in:
#   docker run -v ~/.aws/credentials:/root/.aws/credentials:ro <image>
# See scripts/fetch_granules.py and docs.

CMD ["pixi", "run", "snakemake", "--cores", "1"]
