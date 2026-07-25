# 02 — AIDA Sentence (turbidity limb)

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.

**Form heading:** *"AIDA Sentence — Make structured scientific claims following the AIDA model"*

**Documented field list** (from `docs/forrt-form-fields.md` § AIDA sentence, verbatim):

| Field label | Field type |
|---|---|
| Enter your AIDA sentence here (ending with a full stop) | textarea, **required** |
| Select related topics/tags | dropdown, **optional** |
| Relates to this nanopublication | text input, **required** |
| Supported by datasets | repeatable group, **optional** |
| Supported by other publications | repeatable group, **optional** |

> **This is the turbidity limb.** The Quote (step 01) carries the paper's turbidity/Chl-a
> asymmetry, but an AIDA must be atomic, so it anchors on one limb only. This chain states the
> paper's **turbidity** finding — the strong, positive limb ("high consistency with in situ
> observations, proving the great capabilities of the MSI sensor"). Chlorophyll-a is a separate
> AIDA in the separate `nanopubs/drafts/` set and is not mentioned here.

## Field-by-field draft

<!-- field: aida -->
### AIDA sentence (text input, required)

Atomic, Independent, Declarative, Absolute. One empirical finding. Must end with a full stop.

> _If your draft AIDA contains "and" linking two distinct findings, split into two AIDA nanopubs._

```
Sentinel-2 MSI imagery reliably retrieves turbidity in estuarine waters.
```

> **This is the claim under test, not our result.** The sentence states Sent et al. (2021)'s
> turbidity finding — that MSI turbidity retrieval is the strong, consistent limb ("high
> consistency with in situ observations, proving the great capabilities of the MSI sensor"). Our
> replication numbers (N, R²) live only in `05_outcome.md`; they are deliberately absent here.
> The sentence drops the "turbid" qualifier the Chl-a mirror carries, because "turbidity in
> turbid waters" is circular; "estuarine waters" is the correct, non-circular scope here.
>
> **Pre-write checklist (run per `docs/forrt-form-fields.md` and the AIDA pre-write table):**
> - No numerical values — none. ✓
> - No method names — no processor (Acolite/C2RCC/Polymer), no algorithm (Nechad), no library. "Sentinel-2 MSI" is the sensor under evaluation, not a statistical method. ✓
> - No cryptic identifiers — none. ✓
> - World-talk, not model-talk — states a property of the world (the sensor does reliably measure turbidity there), not "the coefficient/model finds…". ✓
> - One empirical finding — turbidity only; no "and"; chlorophyll-a is a separate AIDA. ✓
> - Ends with a full stop. ✓

<!-- field: topic -->
### Select related topics/tags (search/select, optional)

Wikidata concept labels — the builder resolves each to a QID via `wbsearchentities`.
Each label below was searched and type-checked as a concept (has P279 subclass-of) in this
drafting session; works/persons/places returned by the same searches were rejected
(e.g. the *Estuary* paintings Q20442451 / Q112647535, the Saskatchewan hamlet Q5401883, the
*Remote Sensing* journals, and the turbidity-current thesis/patent).

- turbidity
- remote sensing
- estuary
- Sentinel-2
- water quality

<!-- field: project -->
### Relates to this nanopublication (search/select, required)

URI of the nanopub the AIDA derives from — for this paper-rooted chain, the step 01
Quote-with-comment URI (the same shared Quote as the Chl-a limb).

> **Left empty deliberately — carry-forward.** The chain wizard fills this automatically
> with the published Quote URI once step 01 is published (`docs/chain-draft-contract.md`
> § Carry-forward topology: `01_quote` → `02_aida.project`). Do not hand-fill it; the Quote
> is not yet published (`nanopubs/PUBLISHED.md` step 01 = _not yet published_).

```

```

<!-- field: dataset -->
### Supported by datasets (text input, optional)

DOIs/URLs of datasets that ground the AIDA claim.

*(skip — optional)* The AIDA states the paper's own turbidity claim; the dataset that
grounds it is the AQUASado in situ match-up set, which is request-only (paper Data
Availability Statement, p. 25) and has no citable DOI. Our replication datasets ground the
Outcome, not this claim-under-test, so they belong in step 04/05, not here.

<!-- field: publication -->
### Supported by other publications (text input, optional)

DOIs/URLs of publications that support the AIDA claim.

*(skip — optional)* The source paper (`10.3390/rs13051043`) is already cited via the step 01
Quote-with-comment, so it is not repeated here. Leaving this empty also avoids the known
platform bug that fires when both *Supported by datasets* and *Supported by other
publications* are populated (`docs/forrt-form-fields.md` § AIDA, 2026-04-26).

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 02 (turbidity limb).
