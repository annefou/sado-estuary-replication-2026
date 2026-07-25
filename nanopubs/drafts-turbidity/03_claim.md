# 03 — FORRT Claim

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.

**Form heading:** *"FORRT Claim — Declare an original claim according to FORRT, linking it to an AIDA sentence with a specific FORRT type."*

**Documented field list (from `docs/forrt-form-fields.md` § FORRT Claim, verbatim):**
`Short URI suffix as claim ID` (required) · `Label of the claim (to find it later)` (required) · `Search for an AIDA sentence` (required) · `Type of FORRT claim` (required, 7 options) · `Source URI` (optional). There are no other substantive fields below "Source URI" — only a "publish as example" toggle.

This draft is the **turbidity limb** of the chain (the chlorophyll-a limb is a separate atomic Claim in `nanopubs/drafts/`). It declares, as a FORRT Claim, the paper's turbidity finding that the settled step-02 AIDA states: *"Sentinel-2 MSI imagery reliably retrieves turbidity in estuarine waters."* The Claim is the claim **under test**, i.e. Sent et al. (2021)'s assertion — not our replication result. No numbers here; those live only in `05_outcome.md`.

## Field-by-field draft

<!-- field: claim -->
### Short URI suffix as claim ID (text input, required)

Slug becomes part of the nanopub URI. Use kebab-case.

```
sentinel2-msi-turbidity-retrieval-reliable-estuary
```

<!-- field: label -->
### Label of the claim, to find it later (text input, required)

A descriptive title (not a sentence). Used for searches/discovery.

```
Reliable Sentinel-2 MSI turbidity retrieval in estuarine waters
```

<!-- field: aida -->
### Search for an AIDA sentence (search/select, required)

URI of the AIDA published in step 02.

> **Left empty deliberately — carry-forward.** The chain wizard fills this
> automatically with the published step-02 AIDA URI (`docs/chain-draft-contract.md`
> § Carry-forward topology: `02_aida` → `03_claim.aida`; `build_chain_draft.py`
> override `("03_claim", "aida") → "Search for an AIDA sentence"`). Do not hand-fill
> it; the AIDA is not yet published (`nanopubs/PUBLISHED.md` step 02 = not yet
> published). If the platform search cannot find a Nanodash-published AIDA
> (`w3id.org/np/...` namespace), paste the URI manually at publish time.

```

```

<!-- field: forrtType -->
### Type of FORRT claim (dropdown, required)

Pick one. See `docs/claim-type-vocabulary.md` for the seven options and how to choose.

- [ ] computational performance (Computational & Performance)
- [ ] data governance (access control, licensing, FAIR compliance)
- [ ] data quality (preprocessing, validation, normalization)
- [ ] descriptive pattern (distribution, trend, proportion)
- [x] model performance (accuracy, F1 score, evaluation metrics)
- [ ] scalability (Computational & Performance)
- [ ] statistical significance (significant difference, relationship, or effect)

> **Why `model performance`.** The claim asserts how well a retrieval method — the
> Sentinel-2 MSI plus a bio-optical algorithm, an instrument/model producing
> turbidity estimates — reproduces a known quantity. "Reliably retrieves" is an
> accuracy statement, evidenced by agreement metrics (R², slope, RMSE) between the
> satellite product and an in situ reference. That is a retrieval-accuracy /
> evaluation-metric claim about the retrieval model, which the vocabulary defines as
> *model performance (accuracy, F1 score, evaluation metrics)*. This is the positive
> mirror of the chlorophyll-a limb, which ticked the same type for the same reason:
> both limbs make a claim about how accurately the MSI-plus-algorithm chain retrieves
> a known water-quality parameter — the sign of the verdict differs, the genre does not.
>
> **Not `descriptive pattern`:** that genre is for an observed empirical relationship
> between world variables (e.g. thermal exposure correlates with extirpation). This
> claim is about how accurately a sensor/algorithm measures turbidity, not a natural
> correlation. **Not `statistical significance`:** the claim is not "a test is
> significant"; it is about retrieval reliability. **Not `data quality`:** that covers
> fidelity preserved through a preprocessing transformation (e.g. a DGGS conversion),
> whereas this is end-to-end retrieval accuracy against ground truth. Controlled term
> copied verbatim from `nanopubs/templates/fields.snapshot.json`
> (`model_performance-FORRT-Claim`).

<!-- field: source -->
### Source URI (text input, optional)

Full URL form: `https://doi.org/...` (NOT bare DOI).

> **Metadata — filled by the build script, not hand-filled.** `build_chain_draft.py`
> populates `source` from `CITATION.cff` (`references[article].doi`,
> `10.3390/rs13051043`) as the full URL `https://doi.org/10.3390/rs13051043`
> (`docs/chain-draft-contract.md` § metadata; script line ~199, `source` → external
> URL of the paper DOI). Left empty here so the build script is the single source of
> truth.

```

```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 03 (turbidity limb).
