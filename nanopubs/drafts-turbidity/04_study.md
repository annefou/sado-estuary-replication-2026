# 04 — FORRT Replication Study

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> **Verify code first:** read the actual reproduction script in `notebooks/03_analysis.py` (and `scripts/analysis_core.py`, `scripts/matchup_stats.py`) before writing the methodology field. See `docs/verify-before-drafting.md`.

**Documented field list (from `docs/forrt-form-fields.md` § FORRT Replication Study):**
`Short URI suffix for study ID` (required) · `Label/name of replication study` (required) · `Study type` (required, 3 options) · `Search for a FORRT claim` (required) · `Describe what part of the claim is reproduced/replicated` (required) · `Describe how the claim is reproduced/replicated` (required) · `Describe any deviations from original methodology` (optional) · `Search keywords (Wikidata)` (optional) · `Search discipline (Wikidata)` (optional).

This draft is the **turbidity limb** of the chain (the chlorophyll-a limb is a separate atomic Study in `nanopubs/drafts/04_study.md`). The two limbs share one Quote but anchor on distinct atomic Claims.

## Field-by-field draft

<!-- field: study -->
### Short URI suffix for study ID (text input, required)

Slug. Use kebab-case.

```
turbidity-open-source-westerschelde-replication
```

<!-- field: label -->
### Label/name of replication study (text input, required)

Human-readable title.

```
Open-source Sentinel-2 turbidity retrieval validated against in situ data in the Westerschelde estuary
```

<!-- field: type -->
### Choose the study type (dropdown, required)

- [x] Replication Study - replication with different methodology or conditions
- [ ] Reproduction/Replication Study - study that is both, reproduction and replication
- [ ] Reproduction Study - direct reproduction: same methodology, same tools

> **Why Replication, not Reproduction.** Both the data *and* the methods differ
> from the original: a different estuary and period, a different in situ reference,
> and a different atmospheric-correction processor (Acolite, open source, in place
> of the paper's SNAP-only C2RCC). A direct reproduction is impossible because the
> Sado in situ match-up data are request-only (paper Data Availability Statement)
> and no open substitute exists (`nanopubs/drafts/00b_in_situ_source_scan.md`).

<!-- field: claim -->
### Choose FORRT claim (search/select, required)

URI of the Claim published in step 03. **Carried forward automatically by the chain wizard** from the published step-03 Claim — do not hand-fill. (Registry: `nanopubs/PUBLISHED.md` step 03, currently unpublished.)

```
*(carry-forward — wizard fills from published step 03)*
```

<!-- field: scope -->
### Describe what part of the claim is reproduced/replicated. (textarea, required)

The **scope** of the claim being tested. Which aspect, what's in/out of scope. NOT methodology. NOT results. See `docs/pico-study-outcome-levels.md`.

```
This study tests only the turbidity limb of the original claim: the assertion
that Sentinel-2 MSI retrieval of turbidity is the strong side of a parameter-
dependent accuracy — that turbidity is highly consistent with in situ observations,
demonstrating the sensor's capability to monitor this water quality parameter. In
scope is whether an independent, satellite-derived turbidity product agrees with
coincident in situ turbidity measurements in a mesotidal, well-mixed, turbid
estuary, and whether the original study's strong-turbidity finding still holds when
the retrieval chain is fully open source and transferred to a different estuary and
a longer period. Out of scope, and left to separate atomic chains, are the
chlorophyll-a, suspended-particulate-matter and coloured-dissolved-organic-matter
limbs of the paper's asymmetry, the seasonal time-series analysis, and any
grid-sensitivity (HEALPix / DGGS) representation of the corrected fields.
```

<!-- field: methodology -->
### Describe how the claim is reproduced/replicated. (textarea, required)

The **method** in plain prose. Read `notebooks/03_analysis.py` and `scripts/` first. NOT exact numerical results.

```
The satellite half of the paper's turbidity pipeline is reproduced with a fully
open-source chain (the "aN783" chain) and validated against an independent in situ
reference. Sentinel-2 A/B/C Level-1C granules over the Westerschelde estuary are
atmospherically corrected with Acolite to water-leaving reflectance, clipped to an
estuary bounding box covering the along-axis stations. Turbidity is taken from
Acolite's own native Nechad et al. (2009) turbidity product, the open-source
analogue of the paper's selected turbidity chain; the product is computed by
Acolite with its published relative-spectral-response-convolved Nechad
coefficients rather than a hand-transcribed algorithm, and the near-infrared band
nearest a 783 nm target is selected, matched by nearest wavelength to absorb the
Sentinel-2 A/B/C band-centre drift. At each in situ station a 3x3 pixel window is
cut on the native 10 m UTM grid, with per-pixel quality control (water only, no
cloud/shadow/glint, atmospheric-correction success), and the valid, finite pixels
are averaged. Satellite retrievals are paired with coincident in situ turbidity
from Rijkswaterstaat monitoring stations on station and time within a
plus-or-minus two-hour window. Agreement is scored with the paper's metric suite
(coefficient of determination, slope, intercept, RMSE, bias, unbiased RMS,
absolute and relative percentage difference); unlike the chlorophyll-a limb, the
regression-family metrics for turbidity are computed on untransformed values in
linear space, not in log10 space, since turbidity does not span the orders of
magnitude that motivate the log transform for chlorophyll-a. Statistics are
reported both over the full Sentinel-2 record and over the original study's
field-campaign window, to separate the effect of changing the period from the
effect of changing the site.
```

<!-- field: deviation -->
### Describe any deviations from original methodology. (textarea, optional)

What's different from the original method. Verify against the actual code, don't guess.

```
Five deliberate deviations, each recorded rather than hidden:

1. Atmospheric-correction processor. The paper selected C2RCC for its turbidity
   result (the "cN783" chain, C2RCC + Nechad 2009). C2RCC exists only inside ESA
   SNAP and crashes natively in the container, so it is excluded; this replication
   runs Acolite instead, making the chain "aN783" (Acolite + Nechad 2009), an
   open-source analogue. Note the original study itself reports Acolite as its
   worst-performing atmospheric-correction processor, so a strong turbidity result
   obtained through Acolite here would be a notable outcome rather than an expected
   one.

2. Site. Validation is in the Westerschelde estuary, not the Sado, because the Sado
   in situ match-up data are available only on request (paper Data Availability
   Statement) and no open, contemporaneous, in-estuary substitute exists. The
   Westerschelde is a comparable mesotidal, well-mixed, turbid estuary.

3. Period. The record spans January 2016 to July 2026 (the full Sentinel-2 era),
   not the original's March 2018 to March 2020 field campaign, to gain a more
   complete set of match-ups.

4. In situ reference. Coincident turbidity comes from Rijkswaterstaat routine
   monitoring stations, not the original AQUASado sampling campaign.

5. Fully open-source chain. Every step (Sentinel-2 L1C, Acolite, the native Nechad
   2009 turbidity product) is open and reproducible, whereas the original's
   selected chain depends on the proprietary SNAP/C2RCC processor.
```

<!-- field: keyword -->
### Search keywords (Wikidata) (search/select, optional)

Provide labels (not QIDs) — the Wikidata search picks up labels. Each label resolved via `wbsearchentities` in this session (existence only; the template imposes no type on keyword fields).

- turbidity
- water quality
- estuary
- Sentinel-2
- atmospheric correction

<!-- field: discipline -->
### Search discipline (Wikidata) (search/select, optional)

Provide labels.

- remote sensing

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 04.
