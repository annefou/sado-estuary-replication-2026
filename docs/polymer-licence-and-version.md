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

### Consequence for the pipeline

The Docker image must **not** contain Polymer. Instead:

- `Dockerfile` installs Acolite and C2RCC (SNAP) only.
- Polymer is fetched at **run time** by the user, into a bind-mounted directory, after the
  user has accepted the Hygeos terms themselves.
- `notebooks/01_data_download.py` checks for a `POLYMER_DIR` environment variable and skips
  the Polymer chain with a clear message if it is unset, rather than failing.
- The Polymer leg is therefore **reproducible but not turnkey**. This is a licence
  constraint, not a design flaw, and it must be stated plainly in the Replication Study's
  Methodology field and in `README.md` — the FAIR4RS "Reusable" claim is weaker for this one
  component and pretending otherwise would be dishonest.

Acolite (RBINS, GPLv3) and C2RCC (inside ESA SNAP) carry no such restriction and can both be
baked into the image and archived.

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

### Recommended approach

Run **v4.17.3 as the primary**, and treat the version question as a measurement rather than
an assumption:

- Primary chain: v4.17.3, baseline-04.00-aware, on the reprocessed L1C archive.
- If v4.12 can be made to build, run it as a **sensitivity check** on a subset and report the
  delta. That converts "the version shouldn't matter" from an untested claim into a number.
- Whatever is chosen, the exact tag goes in `pixi.toml`, in the Replication Study's
  Methodology field, and in `README.md`. "We used Polymer" without a version is precisely the
  gap that makes the original hard to reproduce.

Record any observed v4.12-vs-v4.17.3 difference in the Outcome's limitations. A processor
version difference is a legitimate deviation for a Replication Study, but only if declared.
