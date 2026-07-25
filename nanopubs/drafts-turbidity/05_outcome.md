# 05 — FORRT Replication Outcome (TURBIDITY limb)

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> **Verify the actual numerical results first** by reading `results/` and recomputing via `notebooks/04_figures.py`. Don't quote numbers from memory. See `docs/verify-before-drafting.md`.

Documented field list (from `docs/forrt-form-fields.md` § FORRT Replication Outcome):
Short URI suffix for outcome ID · Plain-text label for the outcome · Search for a FORRT replication study · Repository URL · Completion date · Validation status · Confidence level · Describe the overall conclusion about the original claim · Describe the evidence that supports your conclusion · Describe what limits the conclusions of the study.

## Field-by-field draft

<!-- field: outcome -->
### Short URI suffix for outcome ID (text input, required)

Slug. Use kebab-case.

```
turbidity-strong-limb-open-source-westerschelde
```

<!-- field: label -->
### Plain-text label for the outcome (text input, required)

Descriptive title.

```
Open-source Sentinel-2 turbidity retrieval in the Westerschelde confirms the Sado strong-turbidity finding
```

<!-- field: study -->
### Choose study (search/select, required)

URI of the Replication Study published in step 04. Pull from `nanopubs/PUBLISHED.md`.

```
{{STUDY_URI — filled at publish time from nanopubs/PUBLISHED.md step 04; not yet published}}
```

<!-- field: repo -->
### Repository URL (text input, required)

Use the Zenodo **version DOI** URL for the release the results came from — not a
bare branch URL, and not the concept DOI.

> **Why not the bare repo URL.** `https://github.com/ORG/REPO` names a *moving
> branch*. This Outcome asserts "this code produced this number", in a signed,
> immutable record. A branch URL means that assertion points at whatever `main`
> happens to be years from now — code that may never have produced the number
> above. A concept DOI has the same flaw: it resolves to the latest version.
> The version DOI pins the exact release. `docs/chain-decision-tree.md` § Anchor
> ranks the options: SWHID > Zenodo DOI > repo URL > Wayback.
>
> The Zenodo version DOI does not exist until the release is cut; leave the
> placeholder here. `build_chain_draft.py` fills it from `CITATION.cff`
> (identifier described as *"Version DOI"*, recorded automatically at release by
> `.github/workflows/release-identifiers.yml`) at publish time.

```
https://doi.org/{{ZENODO_VERSION_DOI}}
```

<!-- field: date -->
### Choose completion date (text input, required)

```
2026-07-24
```

<!-- field: validationStatus -->
### Choose validation status (dropdown, required)

This dropdown maps to the CiTO intention in step 06: Validated → `confirms`, PartiallySupported → `qualifies`, Contradicted → `disputes`.

- [ ] contradicted
- [ ] inconclusive
- [ ] not tested
- [ ] partially supported
- [x] validated

> **Why `validated` (→ `confirms`).** This is the strong side of the paper's
> parameter asymmetry. Sent et al. (2021) found turbidity to be the *reliably*
> retrievable parameter (their selected cN783 chain, C2RCC + Nechad, R² = 0.84).
> Our fully open-source Acolite + Nechad (aN783) chain, in a different and more
> turbid estuary, meets and slightly exceeds that number (R² = 0.92). The finding
> the paper made — that Sentinel-2 MSI retrieves estuarine turbidity in strong
> agreement with in situ — holds, and holds even when the proprietary C2RCC step
> is replaced by an open-source processor. That is a confirmation, not a
> qualification.

<!-- field: confidenceLevel -->
### Choose confidence level (dropdown, required)

- [x] high - Strong evidence, mostly agrees with original
- [ ] low - Limited evidence, significant disagreement
- [ ] moderate - Adequate evidence, partial agreement
- [ ] very high - Extensive evidence, high agreement with original
- [ ] very low - Minimal evidence, major disagreement

> **Why `high`, not `very high`.** The *direction* of agreement is unambiguous
> and strong — R² = 0.92 meets and exceeds the paper's 0.84, with a near-unity
> slope (0.86). That rules out `moderate` ("partial agreement"), which would
> understate a result that matches the original. But the *strength of evidence*
> is capped by N = 11 match-ups — fewer valid turbidity pairs than the Chl-a limb
> (N = 33), so the R² carries a wide confidence interval. `very high`
> ("extensive evidence") would overclaim on that small sample. `high` weighs both:
> strong agreement, evidence limited in volume.

<!-- field: conclusion -->
### Describe the overall conclusion about the original claim (textarea, required)

Substantive interpretation. Headline comparison: replication's number vs the paper's number, sign + significance.

```
This replication confirms the original claim. Sent et al. (2021) found that
Sentinel-2 MSI retrieves water-quality parameters with parameter-dependent
accuracy — strong for turbidity, weak for chlorophyll-a — and selected a
C2RCC + Nechad (cN783) chain that retrieved turbidity in strong agreement with in
situ (R² = 0.84). Testing that turbidity limb in an independent, more turbid
estuary (the Westerschelde, 2016–2026) with a fully open-source
atmospheric-correction chain (Acolite + Nechad et al. 2010, the aN783 chain), we
obtained strong agreement with in situ turbidity: R² = 0.92 with a near-unity
slope (0.86), meeting and slightly exceeding the paper's proprietary result. This
is the strong side of the parameter asymmetry the paper describes, and it
replicates even open-source: an operationally reproducible chain that uses no
proprietary processor recovers estuarine turbidity at, and slightly beyond, the
accuracy of the paper's selected cN783 chain, in a different optical regime.
```

<!-- field: evidence -->
### Describe the evidence that supports your conclusion (textarea, required)

Numerical results, test statistics, model coefficients. Read directly from `results/`.

```
From results/turbidity_satellite_acolite.parquet, agreement computed in linear
space (scripts/matchup_stats.py), matching the paper's linear treatment of
turbidity (turbidity is reported in FNU on both sides — no unit conversion):

  N = 11 match-ups
  R²    = 0.92   (ours, aN783)      vs  R² = 0.84   (original, selected cN783)
  slope = 0.86   (near unity)
  RMSE  = 10.13  FNU
  BIAS  = +6.91  FNU  (slight overestimate)

The open-source Acolite + Nechad (aN783) chain therefore meets and slightly
exceeds the original study's selected C2RCC + Nechad (cN783) R² of 0.84, with a
near-unity regression slope, in a different and more turbid estuary. The small
positive bias (+6.91 FNU) indicates a mild systematic overestimate but does not
degrade the correlation. Turbidity is the strong side of the parameter asymmetry
seen across the three retrieved parameters. Match-up figure: figures/asymmetry.png.
```

<!-- field: limitations -->
### Describe what limits the conclusions of the study (textarea, optional)

Honest caveats. If the result is partial or contradicted, say so plainly. Don't overclaim.

```
Four factors bound this conclusion.

1. Sample size. N = 11 turbidity match-ups is small — fewer valid pairs than the
   Chl-a limb (N = 33), and comparable to the original (N = 19–21). The R² = 0.92
   therefore carries a wide confidence interval. The direction of the result
   (strong agreement, meeting/exceeding the original) is robust; its precise
   magnitude is not.

2. Processor rating. The paper reports Acolite as its worst-performing
   atmospheric-correction processor, yet here the open-source Acolite + Nechad
   chain matches and slightly exceeds the paper's selected C2RCC + Nechad result.
   That is a notable finding, but a single-site one — it should not be read as a
   general claim that Acolite outperforms C2RCC for turbidity everywhere.

3. Site and period change. This is a Replication, not a Reproduction: the Sado in
   situ data are not public (paper Data Availability Statement), so we validated in
   the Westerschelde (2016–2026), a different and more turbid mesotidal estuary.
   A different optical regime tests generalisability, not the correctness of the
   original analysis. Agreement was computed in linear space, matching the paper's
   treatment of turbidity.

4. Systematic bias. The retrieval carries a slight positive bias (+6.91 FNU), a
   mild overestimate that does not degrade the correlation but should be noted for
   any quantitative use.

A grid-sensitivity check on a HEALPix / DGGS (GRID4EARTH) representation of the
corrected fields is deliberately out of scope here and deferred to a separate
follow-up chain that will extend this one, so the primary validation stays on the
native Sentinel-2 grid.
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 05.
