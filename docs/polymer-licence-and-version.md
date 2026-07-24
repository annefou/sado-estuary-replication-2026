# Polymer — licence constraints and version choice

Project-specific note (not part of the upstream template). Read before writing the
`Dockerfile`, before cutting a Zenodo release, and before pinning a Polymer version.

Source of truth: `LICENCE.TXT` shipped in the repo at
`https://github.com/hygeos/polymer` — **byte-identical at tags `v4.12` and `v4.17.3`**
(verified 2026-07-22). Terms of Use version 2.0, last modified 16 March 2017. The PDF at
`https://hygeos.com/wp-content/uploads/Licence_Polymer.pdf` carries the same operative
clauses. Section 1 makes the website copy authoritative and lets Hygeos amend it at any time,
so **re-check before release**.

## What the licence forbids

Polymer is free for non-commercial scientific research (Sections 2, 8) — but it is *not* open
source, and three clauses bind this repository directly:

| Clause | Effect on this repo |
|---|---|
| **§2** — "may not transfer or sublicense the Software to any third party, in whole or in part, in any form, whether modified or unmodified" | **No Polymer in the Docker image we push to GHCR.** Publishing that image is transfer to third parties. |
| **§10** — Software is "proprietary information and confidential trade secrets"; must not be made available "to any person other than employees of the User" | **No Polymer source in the Zenodo tarball**, and no quoting Polymer source in the Jupyter Book. |
| **§3** — right of use granted "for the country where the User is established" | Each collaborator accepts the terms themselves. A cross-border collaboration cannot rely on one person's acceptance. |
| **§5** — "The User shall notify Hygeos of each modification done by it to the source code" | If we patch Polymer, we must tell Hygeos. Prefer configuration over patching. |
| **§6** — copyright and proprietary notices must be reproduced on every copy | Any vendored file keeps its header. |

## What the licence does NOT restrict — the results are ours

Every clause above governs the **Software**. None governs its **outputs**, and one clause says
so explicitly:

> **§11 (DATA)** — "Hygeos shall not assume any responsibility toward the ownership and rights
> on any data processed through the Software."

Hygeos disclaims any claim over the data Polymer produces. Combined with §2's grant to "use
the Software for the exclusive purpose of scientific research", this means:

**We can freely publish everything Polymer *computes* — water-leaving reflectance (ρw),
Chl-a, match-up statistics, figures, the Outcome nanopub — even though we can never
redistribute the Polymer *code*.** The licence governs the tool, not the numbers.

So Polymer is a **first-class scientific input** to this replication:

- The Polymer + Gons (`pGS`) chain's results appear in the figures and Outcome exactly like
  Acolite's. No licence issue: results, not software.
- Polymer-derived products in the HEALPix / EOPF-Zarr archive (notebook 05) are output data
  (§11 → ours), so they archive to Zenodo freely. **Label them** `source: Polymer vX.Y.Z` in
  the product metadata so an output is never mistaken for redistributable software.
- The **Acolite** chain is turnkey-reproducible from the public image; the **Polymer** chain's
  results are published freely, and a reader reproduces *those specific numbers* by running the
  one opt-in install step (accepting Hygeos's terms as themselves).

Two guardrails that keep the software/results line unambiguous:

1. **Never run Polymer in public CI.** Same reasoning as the public image — keep Polymer
   *execution* to local / opt-in contexts and publish only the results. Public CI runs Acolite.
2. **Tag every Polymer-derived artefact** with its Polymer version in metadata, so provenance
   is traceable and no output is ever confused for the tool.

### Consequence for the pipeline — we *can* still have Docker

The licence restricts **distribution**, not **containerisation**. The distinction matters and
is easy to get backwards:

| Action | Allowed? | Why |
|---|---|---|
| Build a local image containing Polymer, for your own use | **Yes** | §6 permits copies "as necessary for use by the User" |
| Run that image on your own machines / your institution's | **Yes** | §10 permits access by "employees of the User" |
| Push that image to **public GHCR**, Docker Hub, or Zenodo | **No** | §2 transfer to third parties; §10 disclosure |
| Publish an image *without* Polymer | **Yes** | Nothing restricted is inside it |

So the design is:

- **The published image** (`.github/workflows/docker.yml` → GHCR) contains the full pipeline
  **minus Polymer**: Acolite, C2RCC/SNAP, and everything else. It is complete and runnable
  for two of the three atmospheric-correction chains.
- **Polymer is an opt-in pixi feature.** v4.17.3 ships `pyproject.toml` + `meson.build` and
  is `pip install`-able straight from the tag, so it belongs in an optional feature rather
  than a bind mount:

  ```toml
  # pixi.toml — opt-in; the user fetches Polymer directly from Hygeos and
  # accepts the Hygeos Terms of Use by doing so. We never redistribute it.
  [feature.polymer.pypi-dependencies]
  polymer = { git = "https://github.com/hygeos/polymer.git", tag = "v4.17.3" }

  [environments]
  polymer = { features = ["polymer"], solve-group = "default" }
  ```

  `pixi run -e polymer …` enables the third chain. The default environment does not, and
  `03_analysis.py` skips the Polymer chain with a clear message rather than failing.

  This is the honest mechanism: each user pulls Polymer **from Hygeos**, not from us, which
  is also what §3 requires — the licence is granted per-user, for the user's own country.

- The Polymer leg is therefore **reproducible but not turnkey**, and that must be stated in
  the Replication Study's Methodology field and in `README.md`. The FAIR4RS "Reusable" claim
  is genuinely weaker for this one component; pretending otherwise would be dishonest.

Acolite (RBINS, GPLv3) and C2RCC (inside ESA SNAP) carry no such restriction and can both be
baked into the published image and archived on Zenodo.

### How much does a Polymer-free public image actually cost us?

Less than it first appears. From `00_paper_summary.md`, **every chain the original study
selected for its time series is C2RCC-based**: `cT443` (aCDOM), `cGS` (Chl-a), `cN740` (SPM),
`cN783` (turbidity). Polymer appears in the paper only as one arm of the three-way
atmospheric-correction *intercomparison*, where it was best-overall for aCDOM (R² 0.608) and
SPM (R² 0.57).

For this replication specifically:

| Component | Needs Polymer? |
|---|---|
| **Chl-a limb — the frozen chain anchor** (best chain `cGS` = AC-C2RCC + Gons 2005) | **No** |
| SPM time-series chain (`cN740` = AC-C2RCC + Nechad 740) | **No** |
| Three-way AC processor intercomparison (incl. "Acolite is biased high") | **Yes** |

So the **public GHCR image reproduces the headline analysis end-to-end, turnkey**. The
claim this chain is anchored on does not touch Polymer at all. Only the processor
intercomparison — a secondary finding — needs the opt-in environment.

That is a comfortable place to land: the restricted component sits outside the critical path,
and its absence from the public image degrades breadth, not the central result.

### If full turnkey coverage is wanted anyway

§10 forbids disclosure "without the prior written consent of Hygeos" — which means consent
*can* be granted. Asking Hygeos for written permission to redistribute Polymer inside a
public, non-commercial replication image is a reasonable request, and a "yes" would remove
the caveat entirely. Worth doing in parallel; do not block on it, and do not ship a
Polymer-bearing public image before written consent is in hand.

## Version choice — v4.12 is *not* a safe default

The original study used **Polymer v4.12**. Matching it sounds like the conservative choice for
a replication, and for a *Reproduction* it would be. It is not safe here, for four reasons
taken from `CHANGELOG.TXT`:

1. **Sentinel-2 processing baseline 04.00 (the big one).** v4.15 adds *"Support MSI
   processing baseline 4.00 (account for the offset in TOA reflectance)"*. ESA introduced a
   radiometric offset in L1C TOA reflectance with baseline 04.00 and **reprocessed the whole
   archive**. Data downloaded today for 2018–2020 therefore arrives on the new baseline even
   though it predates it. **v4.12 does not know about the offset and would silently produce
   biased water reflectance on exactly the data we intend to use.** This alone rules out
   naive use of v4.12.
2. **ERA5 / CDS migration.** v4.17 notes *"ERA5: compatibility with new CDS"*. The legacy
   Climate Data Store API was retired; v4.12's ancillary fetching may simply not run today.
3. **Turbid-water processing improved.** v4.15 added the experimental `minabs2` mode for
   complex coastal and inland waters, updated for MSI in v4.16 — directly relevant to a
   turbid estuary, and an option the original authors never had.
4. **Build system.** v4.17 moved to `meson`, is `pip install`-able, and **supports pixi
   natively** — which matches this template's stack. v4.12 uses the old makefile/cython build
   and may not compile against current toolchains.

Points 3 and 4 are conveniences. **Point 1 is a correctness issue** and point 2 is a
will-it-run issue.

### Decision (2026-07-22): pin `v4.17.3`

`v4.17.3` is the newest tag (commit dated 2026-01-09) and is the pinned primary version.
Polymer v5 is described by Hygeos as "in development"; the v4/v5 codebases coexist inside
v4.17.x, and we use the **v4 API** — do not drift onto the v5 framework mid-study.

- Primary chain: **v4.17.3**, baseline-04.00-aware, on the reprocessed L1C archive.
- If v4.12 can be made to build, run it as a **sensitivity check** on a subset and report the
  delta. That converts "the version shouldn't matter" from an untested claim into a number.
  If it cannot be built (likely — old cython/makefile build, retired CDS API), say so rather
  than quietly dropping the comparison.
- The exact tag goes in `pixi.toml`, in the Replication Study's Methodology field, and in
  `README.md`. "We used Polymer" without a version is precisely the gap that makes the
  original study hard to reproduce — not repeating it is part of the point of this
  replication.

Record any observed v4.12-vs-v4.17.3 difference in the Outcome's limitations. A processor
version difference is a legitimate deviation for a Replication Study, but only if declared.
