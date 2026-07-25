# 04 — FORRT Replication Study

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> **Verify code first:** read the actual reproduction script in `notebooks/03_analysis.py` before writing the methodology field. See `docs/verify-before-drafting.md`.

**Documented field list (from `docs/forrt-form-fields.md` § FORRT Replication Study):**
`Short URI suffix for study ID` (required) · `Label/name of replication study` (required) · `Study type` (required, 3 options) · `Search for a FORRT claim` (required) · `Describe what part of the claim is reproduced/replicated` (required) · `Describe how the claim is reproduced/replicated` (required) · `Describe any deviations from original methodology` (optional) · `Search keywords (Wikidata)` (optional) · `Search discipline (Wikidata)` (optional).

This draft is the **chlorophyll-a limb** of the chain (the turbidity limb is a separate atomic Study).

## Field-by-field draft

<!-- field: study -->
### Short URI suffix for study ID (text input, required)

Slug. Use kebab-case.

```
chla-open-source-westerschelde-replication
```

<!-- field: label -->
### Label/name of replication study (text input, required)

Human-readable title.

```
Open-source Sentinel-2 chlorophyll-a retrieval validated against in situ data in the Westerschelde estuary
```

<!-- field: type -->
### Choose the study type (dropdown, required)


> **Why Replication, not Reproduction.** Both the data *and* the methods differ
> from the original: a different estuary and period, a different in situ reference,
> and a different atmospheric-correction processor (Acolite, open source, in place
> of the paper's SNAP-only C2RCC). A direct reproduction is impossible because the
> Sado in situ match-up data are request-only (paper Data Availability Statement)
> and no open substitute exists (`nanopubs/drafts/00b_in_situ_source_scan.md`).

- [x] Replication Study - replication with different methodology or conditions
- [ ] Reproduction/Replication Study - study that is both, reproduction and replication
- [ ] Reproduction Study - direct reproduction: same methodology, same tools

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
This study tests only the chlorophyll-a limb of the original claim: the assertion
that Sentinel-2 MSI retrieval of chlorophyll-a is the weak side of a parameter-
dependent accuracy — that chlorophyll-a is the parameter for which further research
and a more complete set of match-ups are still needed. In scope is whether an
independent, satellite-derived chlorophyll-a product agrees with coincident in situ
chlorophyll-a measurements in a mesotidal, well-mixed, turbid estuary, and whether
the original study's weak-chlorophyll-a caution still holds when the retrieval chain
is fully open source and transferred to a different estuary and a longer period.
Out of scope, and left to separate atomic chains, are the turbidity, suspended-
particulate-matter and coloured-dissolved-organic-matter limbs of the paper's
asymmetry, the seasonal time-series analysis, and any grid-sensitivity (HEALPix /
DGGS) representation of the corrected fields.
```

<!-- field: methodology -->
### Describe how the claim is reproduced/replicated. (textarea, required)

The **method** in plain prose. Read `notebooks/03_analysis.py` and any config files first. NOT exact numerical results.

```
The satellite half of the paper's pipeline is reproduced with a fully open-source
chain (the "aGS" chain) and validated against an independent in situ reference.
Sentinel-2 A/B/C Level-1C granules over the Westerschelde estuary are
atmospherically corrected with Acolite to water-leaving reflectance, clipped to an
estuary bounding box covering the along-axis stations. Chlorophyll-a is retrieved
with the Gons et al. (2005) red-edge three-band algorithm, using the 665, 705 and
783 nm bands, transcribed from the original paper's Table 2; the bands are matched
by nearest wavelength to absorb the Sentinel-2 A/B/C band-centre drift. At each in
situ station a 3x3 pixel window is cut on the native 10 m UTM grid, with per-pixel
quality control (water only, no cloud/shadow/glint, atmospheric-correction success),
and the valid pixels are averaged. Satellite retrievals are paired with coincident
in situ chlorophyll-a from Rijkswaterstaat monitoring stations on station and time
within a plus-or-minus two-hour window. Agreement is scored with the paper's metric
suite (coefficient of determination, slope, intercept, RMSE, bias, unbiased RMS,
absolute and relative percentage difference), with the regression-family metrics
computed in log10 space for chlorophyll-a and the percentage-difference metrics on
untransformed values, exactly as the original specifies. Statistics are reported
both over the full Sentinel-2 record and over the original study's field-campaign
window, to separate the effect of changing the period from the effect of changing
the site.
```

<!-- field: deviation -->
### Describe any deviations from original methodology. (textarea, optional)

What's different from the original method. Verify against the actual code, don't guess.

```
Five deliberate deviations, each recorded rather than hidden:

1. Atmospheric-correction processor. The paper selected C2RCC for its chlorophyll-a
   time series (the "cGS" chain, C2RCC + Gons). C2RCC exists only inside ESA SNAP
   and crashes natively in the container, so it is excluded; this replication runs
   Acolite instead, making the chain "aGS" (Acolite + Gons), an open-source
   analogue. Note the original study itself reports Acolite as its worst-performing
   processor.

2. Site. Validation is in the Westerschelde estuary, not the Sado, because the Sado
   in situ match-up data are available only on request (paper Data Availability
   Statement) and no open, contemporaneous, in-estuary substitute exists. The
   Westerschelde is a comparable mesotidal, well-mixed, turbid estuary.

3. Period. The record spans January 2016 to July 2026 (the full Sentinel-2 era),
   not the original's March 2018 to March 2020 field campaign, to gain the "more
   complete set of match-ups" the paper called for.

4. In situ reference. Coincident chlorophyll-a comes from Rijkswaterstaat routine
   monitoring stations, not the original AQUASado sampling campaign.

5. Fully open-source chain. Every step (Sentinel-2 L1C, Acolite, the Gons algorithm)
   is open and reproducible, whereas the original's selected chain depends on the
   proprietary SNAP/C2RCC processor.
```

<!-- field: keyword -->
### Search keywords (Wikidata) (search/select, optional)

Provide labels (not QIDs) — the Wikidata search picks up labels.

- chlorophyll a  *(Wikidata Q133878, confirmed resolves — chemical compound)*
- water quality  *(Wikidata Q625376, confirmed resolves)*
- estuary  *(Wikidata Q47053, confirmed resolves — marine and riverine ecosystem)*
- Sentinel-2  *(Wikidata Q4302480, confirmed resolves — Earth observation satellite)*
- atmospheric correction  *(Wikidata Q4817104, confirmed resolves — image-processing technique)*

<!-- field: discipline -->
### Search discipline (Wikidata) (search/select, optional)

Provide labels.

- remote sensing  *(Wikidata Q199687, confirmed resolves — academic discipline)*

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 04.
