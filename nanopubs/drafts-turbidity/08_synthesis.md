# 08 — Research Synthesis (optional)

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> Use this template only when this chain is **one of several** testing facets of a shared underlying property. The Synthesis names the cross-cutting conclusion and lists the multiple Outcomes as supporting sources.

**Form heading:** *"Science Live Research Synthesis — Synthesise findings across multiple replication outcomes with conclusions, recommendations, conditions, and limitations."*

> **Why this synthesis is legitimate — and does not break the atomic-AIDA rule.**
> This chain has TWO atomic limbs, each with its own AIDA / Claim / Study / Outcome:
> a **chlorophyll-a** limb (Outcome `chla-weak-limb-open-source-westerschelde`, verdict
> `partially supported` → `qualifies`) and a **turbidity** limb (Outcome
> `turbidity-strong-limb-open-source-westerschelde`, verdict `validated` → `confirms`).
> The Research Synthesis sits ABOVE both and composes them into the paper's headline
> finding — retrieval accuracy is *parameter-dependent*. A synthesis is *defined* to
> compose multiple findings, so the compound "turbidity strong AND chlorophyll-a weak"
> statement legitimately lives here. The atomic-AIDA rule governs the AIDA sentences one
> level down, which stay single-finding; it does not govern this node.

## Field-by-field draft

<!-- field: synthesis -->
### Short URI suffix for synthesis ID (text input, required)

Slug. Use kebab-case.

```
sentinel2-parameter-asymmetry-open-source-westerschelde
```

<!-- field: label -->
### Label (text input, required)

A one-line summary.

```
Open-source Sentinel-2 reproduces the parameter-dependent water-quality retrieval asymmetry in the Westerschelde
```

<!-- field: conclusion -->
### Conclusion of the synthesis (textarea, required)

The aggregate finding across the underlying outcomes.

```
Sent et al. (2021) reported that Sentinel-2 MSI retrieves estuarine water-quality
parameters with parameter-dependent accuracy — strong for turbidity, weak for
chlorophyll-a. This synthesis composes two independent replication limbs and finds
that the asymmetry itself is what replicates. In an independent, more turbid estuary
(the Westerschelde) and with a fully open-source atmospheric-correction chain
(Acolite), the two parameters behave exactly as the paper's asymmetry predicts, but
they land on opposite verdicts. The turbidity limb CONFIRMS the paper: the open-source
Acolite + Nechad (aN783) chain retrieves in situ turbidity in strong agreement,
R² = 0.92 with a near-unity slope (0.86), meeting and slightly exceeding the paper's
proprietary C2RCC + Nechad (cN783) result of R² = 0.84. The chlorophyll-a limb
QUALIFIES the paper's own caution: the open-source Acolite + Gons (aGS) chain achieves
no useful agreement with in situ chlorophyll-a, R² = 0.10 (log10 space), far below the
paper's selected C2RCC + Gons (cGS) result of R² = 0.63, deepening rather than
resolving the weakness the original authors flagged. The composed, replicated result
is therefore not a single accuracy number but a structural property: Sentinel-2
water-quality retrieval accuracy is parameter-dependent, and that dependence survives
both a change of estuary and the replacement of the proprietary processor by an
open-source one.
```

<!-- field: recommendation -->
### Recommendations (textarea, required)

Actionable guidance for practitioners.

```
1. Do not treat "Sentinel-2 water-quality retrieval" as a single capability. Validate
   and report accuracy per parameter: a chain trustworthy for turbidity can be
   simultaneously unreliable for chlorophyll-a in the same water.

2. For estuarine turbidity monitoring (e.g. Water Framework Directive reporting), a
   fully open-source Acolite + Nechad chain is a viable, citable alternative to the
   proprietary C2RCC processor — here it matched and slightly exceeded the proprietary
   result in a different estuary.

3. For estuarine chlorophyll-a, treat MSI retrievals in turbid Case-2 water as
   provisional. The paper's call for "a more complete set of match-ups" stands; collect
   more coincident in situ pairs and validate locally before any operational use, and do
   not assume a red-edge algorithm is tracking pigment rather than backscatter.

4. Prefer open-source, operationally reproducible processing chains for replication and
   monitoring: they make the retrieval auditable end-to-end and, on the turbidity limb
   here, cost nothing in accuracy.
```

<!-- field: conditions -->
### Conditions under which the synthesis applies (textarea, required)

Scope: data types, methods, domains, regions, time periods.

```
This synthesis holds within the following scope:

- Domain and site: a turbid, mesotidal, well-mixed temperate estuary — the Westerschelde
  (Netherlands). It generalises to comparable optically complex Case-2 estuaries, not to
  clear open-ocean (Case-1) water.
- Processing chain: the fully open-source Acolite atmospheric correction with the Gons
  et al. (2005) red-edge algorithm for chlorophyll-a (aGS) and the Nechad et al. (2010)
  algorithm for turbidity (aN783). This is NOT the paper's proprietary C2RCC chain
  (cGS / cN783); the synthesis compares an open-source chain against the paper's
  proprietary result and does not re-run C2RCC.
- Sensor and period: Sentinel-2 MSI (A/B/C era), imagery 2016–2026.
- Reference: coincident Rijkswaterstaat in situ observations at along-axis stations;
  turbidity compared in linear space (FNU on both sides, no unit conversion),
  chlorophyll-a compared in log10 space, matching the paper's treatment of each.
- Sample sizes: small — turbidity N = 11 match-ups, chlorophyll-a N = 33. The direction
  of each verdict is robust; precise magnitudes carry wide uncertainty.
- Design: a Replication (different site, different period, open-source processor), not a
  Reproduction — the Sado in situ data are not public.
- Out of scope: grid-sensitivity of the retrieval (a HEALPix / DGGS GRID4EARTH
  representation of the corrected fields) is deferred to a separate follow-up chain that
  will extend this one; the primary validation stays on the native Sentinel-2 grid.
```

<!-- field: limitations -->
### Limitations of the synthesis (textarea, required)

What was not tested? What might not generalise?

```
1. Not a head-to-head processor test. The paper's headline numbers (cGS R² = 0.63,
   cN783 R² = 0.84) are the proprietary C2RCC chain, which was never run here (C2RCC
   exists only inside ESA SNAP and crashes in the container). The synthesis compares an
   open-source chain against the paper's published proprietary result; it does not prove
   the open-source chain equals C2RCC on the same imagery. In particular, the finding
   that open-source Acolite matches C2RCC for turbidity is a single-site observation, not
   a general claim that Acolite outperforms C2RCC everywhere.

2. Small samples. With N = 11 (turbidity) and N = 33 (chlorophyll-a), each R² carries a
   wide confidence interval. The composed asymmetry is qualitatively robust across the
   two limbs; the exact R² values should not be over-read.

3. Single estuary, single reference network. Both limbs were validated in one
   Westerschelde record against one in situ provider. Whether the parameter-dependent
   asymmetry holds in structurally different estuaries, or against other reference
   networks, was not tested here.

4. Retrieval bias not corrected. The turbidity retrieval carries a slight positive bias
   (+6.91 FNU) and the chlorophyll-a retrieval a positive bias with a negative slope;
   these are reported, not corrected, and would matter for any quantitative use.

5. Grid representation untested. Any sensitivity of these verdicts to spatial
   re-gridding (HEALPix / DGGS) is explicitly out of scope and deferred to a follow-up
   chain.
```

<!-- field: date -->
### Completion date (text input, required)

```
2026-07-24
```

<!-- field: source -->
### Supporting sources (text input, required)

Each entry is a URL — typically the FORRT Outcome URIs being synthesised. Pull from `nanopubs/PUBLISHED.md` (and/or registries from sibling repos).

> **Carry-forward — TWO Outcome URIs, one auto-wired, one added by hand.** This synthesis
> lives in the **turbidity** chain — the last limb published — so both Outcome URIs are
> available when it publishes:
>
> 1. **Turbidity Outcome** (`nanopubs/drafts-turbidity/05_outcome.md`,
>    `turbidity-strong-limb-open-source-westerschelde`) — **auto-wired.** `build_chain_draft.py`
>    carries THIS chain's just-published Outcome URI into `sources` automatically (the
>    `05_outcome → 08_synthesis` edge). Leave it for the wizard.
> 2. **Chlorophyll-a Outcome** (`chla-weak-limb-open-source-westerschelde`) — **ADD MANUALLY.**
>    The Chl-a limb is a separate chain that was published first, so its Outcome URI is already
>    known. At the synthesis step, paste it as a SECOND `source` row in the wizard (from the URI
>    the Chl-a wizard returned / `nanopubs/PUBLISHED.md` step 05).

<!-- field: topic -->
### Topic (search/select, required)

Provide labels (not QIDs). Each label below was resolved against the Wikidata API in this
drafting session and confirmed to be a concept (P279 subclass-of present): turbidity
(Q898574), chlorophyll a (Q133878), remote sensing (Q199687), estuary (Q47053), Sentinel-2
(Q4302480, P279 → Q854845), water quality (Q625376).

- _Label 1: turbidity
- _Label 2: chlorophyll a
- _Label 3: remote sensing
- _Label 4: estuary
- _Label 5: Sentinel-2
- _Label 6: water quality

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 08.
