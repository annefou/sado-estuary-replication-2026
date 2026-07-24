# Atmospheric-correction processor choice — a declared deviation

The original study (Sent et al. 2021) compared three atmospheric-correction (AC)
processors — **Acolite**, **C2RCC**, and **Polymer** — and selected **C2RCC + Gons
et al. 2005** (`cGS`) as its chain for the Chl-a time series. This replication
uses **Acolite + Gons** (`aGS`) as its primary chain, with **Polymer + Gons**
(`pGS`) as an opt-in second processor, and **excludes C2RCC**. This note records
why, because it is a methodological deviation that must be stated in the
Replication Study's Methodology field and the Outcome's limitations.

## Why C2RCC is excluded

C2RCC is a neural-network AC that exists **only** inside ESA SNAP, a ~2 GB Java
desktop application. There is no Python-native C2RCC (checked: nothing on PyPI,
no maintained reimplementation). Running it means shipping and running SNAP.

Four container iterations (the `ac-probe` workflow, branch history on
`fix-ac-probe`) established that **C2RCC crashes in-container even when correctly
configured**:

- SNAP 11 requires Java 11; the base image's system Java is 21. Running C2RCC on
  Java 21 segfaults.
- Pinning SNAP's `gpt` launcher to the bundled Java 11 (`INSTALL4J_JAVA_HOME`)
  was verified to work — the crash log then reads `Java VM: OpenJDK ... 11.0.19`.
- It **still** segfaults, now natively: `Problematic frame: C [libc.so.6]`. This
  is a known SNAP-in-Docker failure mode (SNAP's bundled native libraries against
  the container's), not something fixable from our side.

Keeping SNAP would buy only a processor that will not run, at the cost of a heavy,
fragile, Java-dependent image. SNAP was therefore removed entirely; the container
is pure-Python.

## Why this is scientifically sound

The claim under test is the **Chl-a limb** of the paper's asymmetry: does
Sentinel-2 MSI retrieve chlorophyll-a well or poorly in a turbid, well-mixed
mesotidal estuary? That is a question about the sensor and the water, not about
one AC processor. Two points support the choice:

1. **The paper's own evidence makes the Chl-a verdict processor-robust.** Even its
   *selected best* chain (`cGS`) had a Chl-a time-series mean APD of ~391 %. Chl-a
   was hard across all three processors; the verdict does not rest on C2RCC.
2. **Two independent processors guard against confounding the AC with the
   verdict.** Acolite and Polymer are both Python-native and both evaluated by the
   paper. If both agree on the Chl-a verdict, it is robust to processor choice; if
   they disagree, that is itself an informative result. The paper rated Acolite
   worst (biased high) and Polymer best in the Sado — so testing whether that
   ranking holds in the Westerschelde is part of the replication, not a gap.

The exclusion is also, for an Open Science / FAIR replication, a finding in its
own right: **the original study's selected chain is locked behind aging Java
tooling that does not containerise reliably.** That is a reproducibility
observation worth stating, not a weakness to hide.

## What the reader gets

- **Acolite + Gons (`aGS`)** — the primary chain, fully reproducible from the
  public container (turnkey).
- **Polymer + Gons (`pGS`)** — a second processor. Polymer's licence keeps it out
  of the public image, so its *results* are published while a reader reproduces
  those specific numbers via the one opt-in install step
  (`docs/polymer-licence-and-version.md`).
- **C2RCC** — not run; reason as above. If a future SNAP release fixes the native
  crash, C2RCC could be added as a third chain without changing the anchor.
