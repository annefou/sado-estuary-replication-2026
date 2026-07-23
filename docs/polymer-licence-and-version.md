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
