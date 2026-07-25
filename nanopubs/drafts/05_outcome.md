# 05 — FORRT Replication Outcome

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> **Verify the actual numerical results first** by reading `results/` and `notebooks/03_analysis.py`. Don't quote numbers from memory. See `docs/verify-before-drafting.md`.

## Field-by-field draft

<!-- field: outcome -->
### Short URI suffix for outcome ID (text input, required)

Slug. Use kebab-case.

```
chla-weak-limb-open-source-westerschelde
```

<!-- field: label -->
### Plain-text label for the outcome (text input, required)

Descriptive title.

```
Open-source Sentinel-2 chlorophyll-a retrieval in the Westerschelde qualifies the Sado weak-Chl-a finding
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
> Both DOIs and the SWHID are in `CITATION.cff` under `identifiers:`, recorded
> automatically at release by `.github/workflows/release-identifiers.yml`. Take
> the one described as *"Version DOI"*.

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


> **Why `partially supported` (→ `qualifies`), not `contradicted`.** The paper's
> Chl-a claim is a *caution*: Chl-a is the weak parameter, "further research is
> needed." Our open-source `aGS` chain finding no useful Chl-a agreement (R²≈0.10)
> **supports and extends** that caution — it is not evidence the paper is wrong.
> A `contradicted`/`disputes` label would overclaim: we never ran the paper's
> selected `cGS` (C2RCC) chain, and the paper itself reports Acolite as its worst
> processor, so a weaker `aGS` result is partly anticipated. See the limitations
> field and `docs/claim-type-vocabulary.md`.

- [ ] contradicted
- [ ] inconclusive
- [ ] not tested
- [x] partially supported
- [ ] validated

<!-- field: confidenceLevel -->
### Choose confidence level (dropdown, required)

- [ ] high - Strong evidence, mostly agrees with original
- [ ] low - Limited evidence, significant disagreement
- [x] moderate - Adequate evidence, partial agreement
- [ ] very high - Extensive evidence, high agreement with original
- [ ] very low - Minimal evidence, major disagreement

<!-- field: conclusion -->
### Describe the overall conclusion about the original claim (textarea, required)

Substantive interpretation. Headline comparison: replication's number vs the paper's number, sign + significance.

```
This replication qualifies the original claim. Sent et al. (2021) found that
Sentinel-2 MSI retrieves water-quality parameters with parameter-dependent
accuracy — strong for turbidity but weak for chlorophyll-a, concluding that "for
the key parameter Chl-a further research is needed, with a more complete set of
match-ups." Testing that chlorophyll-a limb in an independent, more turbid estuary
(the Westerschelde, 2016–2026) with a fully open-source atmospheric-correction
chain (Acolite + Gons et al. 2005, the aGS chain), we obtained no useful agreement
with in situ chlorophyll-a: R² = 0.10 over the full record (N = 33) and R² = 0.13
for the 2018–2020 subset (N = 14), with a negative regression slope and a positive
bias. This does not confirm that an operationally reproducible, open-source chain
can retrieve estuarine chlorophyll-a at the accuracy of the paper's selected cGS
chain (R² = 0.63, C2RCC + Gons). Rather than contradicting the paper, the result
supports and extends its central caution: chlorophyll-a is the parameter for which
MSI retrieval is not yet reliable, and that weakness persists — indeed deepens —
when the proprietary C2RCC step is replaced by an open-source processor and the
method is transferred to a different optical regime.
```

<!-- field: evidence -->
### Describe the evidence that supports your conclusion (textarea, required)

Numerical results, test statistics, model coefficients. Read directly from `results/`.

```
From results/chla_satellite_acolite.parquet, agreement computed in log10 space
(scripts/matchup_stats.py), matching the paper's log-scale treatment of Chl-a:

  Full record (2016–2026):        N = 33, R² = 0.10, slope = −0.20,
                                  RMSE = 0.63 (log10), BIAS = +0.40
  Original-window subset (2018–2020): N = 14, R² = 0.13, slope = −0.14,
                                  RMSE = 0.59 (log10), BIAS = +0.30

Satellite chlorophyll-a (median 8.7 µg/L, range 1.9–27.7) systematically exceeds
the coincident Rijkswaterstaat in situ chlorophyll-a (median 3.1 µg/L, range
0.9–26.0) across six along-axis stations. The negative slope is the decisive
feature: the retrieval does not track in situ chlorophyll-a at all, consistent with
the Gons red-edge algorithm responding to backscatter/turbidity rather than pigment
in this high-SPM estuary. For comparison, the original study's selected cGS chain
reported R² = 0.63. Match-up figure: figures/main_result.png.
```

<!-- field: limitations -->
### Describe what limits the conclusions of the study (textarea, optional)

Honest caveats. If the result is partial or contradicted, say so plainly. Don't overclaim.

```
Three factors bound this conclusion and must be read together.

1. Processor change. The paper's headline Chl-a number (R² = 0.63) is the cGS
   chain (C2RCC + Gons). We ran the aGS chain (Acolite + Gons) because C2RCC exists
   only inside ESA SNAP and crashes natively in the container
   (docs/atmospheric-correction-choice.md). We therefore did not test cGS and
   cannot dispute its number. The paper itself reports Acolite as its worst-
   performing processor (mean BIAS 2.78, mean APD 254 percent), so a weaker aGS
   result is partly anticipated by the original study — a reason this is a
   qualification, not a contradiction.

2. Site and period change. This is a Replication, not a Reproduction: the Sado
   in situ data are not public (paper Data Availability Statement), so we validated
   in the Westerschelde (2016–2026), a different and more turbid mesotidal estuary.
   A different optical regime tests generalisability, not the correctness of the
   original analysis. We report both the full record and the 2018–2020 subset to
   separate the period change from the site change as far as the data allow.

3. Sample size. N = 33 (14 in the original window) over six stations is small — as
   in the original (N = 19–21) — so every R² carries wide uncertainty. The
   direction of the result (no useful agreement) is robust; its precise magnitude
   is not.

A grid-sensitivity check on a HEALPix / DGGS (GRID4EARTH) representation of the
corrected fields is deliberately out of scope here and deferred to a separate
follow-up chain that will extend this one, so the primary validation stays on the
native Sentinel-2 grid.
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 05.
