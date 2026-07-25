# 06 — CiTO Citation (turbidity limb)

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.

**Form heading:** *"Declare citations between papers or other works, using Citation Typing Ontology"*

**Documented field list** (from `docs/forrt-form-fields.md` § Citation with CiTO, template key `CITATION_CITO`):

| Field label | Field type | Notes |
|---|---|---|
| Identifier for the citing creative work | text input, **required** | The citing work = this chain's step-05 Outcome nanopub URI. |
| List citations | repeatable group, **required** ≥1 | Platform form field `st02` = array of `{ cites, cited }` (see `docs/chain-draft-contract.md`), not flat `cites`/`cited`. |
| ↳ Citation Type | dropdown | A CiTO relation URI from the controlled list. |
| ↳ DOI or other URL of the cited work | text input | DOI URL form `https://doi.org/10.x/y`. |

> **Scope:** this CiTO citation closes the **turbidity limb** only. The chlorophyll-a limb has its own separate CiTO citation. Do not fold the two into one.

## Field-by-field draft

<!-- field: work -->
### Identifier for the citing creative work (text input, required)

**CARRY-FORWARD — leave empty.** The citing work is the step-05 Replication
Outcome nanopub, whose URI does not exist until that step is published. The chain
wizard fills this automatically from the URI it captured when publishing step 05
(carry-forward `05_outcome` → `06_citation`, field `work`; see
`docs/chain-draft-contract.md` § Carry-forward topology). Do not hand-write it.

```

```

### List citations (repeatable group `st02`, required ≥1)

One citation row. Per the contract the platform field is `st02`, an array of
`{ cites, cited }` objects. This limb needs exactly one row:

```
st02 = [
  {
    "cites": "http://purl.org/spar/cito/confirms",
    "cited": "https://doi.org/10.3390/rs13051043"
  }
]
```

#### Citation 1 — back to the original paper

##### Citation Type (dropdown) — `cites`

**Value: `confirms`** → `http://purl.org/spar/cito/confirms`

Derived from the step-05 Outcome's validation status. `05_outcome.md` records the
status as **validated**, and the documented mapping is
Validated → `confirms` (`docs/forrt-form-fields.md` § Mapping rule for
FORRT Outcomes; `05_outcome.md` line 78). `build_chain_draft.py` fills this field
itself, reading the Outcome status and applying
`RELATION_FROM_STATUS["Validated"] = cito/confirms` — so the value below
is not hand-authored into `st02`, it is derived. It is recorded here for review.

**Justification:** the open-source `aN783` chain (Acolite + Nechad et al. 2010)
reproduces the paper's strong turbidity finding in an independent, more turbid
estuary (the Westerschelde), obtaining R² = 0.92 with a near-unity slope — meeting
and slightly exceeding the paper's selected `cN783` (C2RCC + Nechad) result of
R² = 0.84. The paper made turbidity its reliably retrievable parameter, and that
finding holds even when the proprietary C2RCC step is replaced by an open-source
processor. The result therefore *supports and reproduces* the paper's finding
rather than merely refining it: `confirms`, not `qualifies`.

```
http://purl.org/spar/cito/confirms
```

##### DOI or other URL of the cited work (text input) — `cited`

**METADATA — filled from `CITATION.cff` by the build script.** `cited` is the
replicated paper, taken from `CITATION.cff` → `references` (type `article`) → `doi`
(`10.3390/rs13051043`) and emitted in URL form. `build_chain_draft.py` fills this
via `metadata_value("06_citation", "cited")`. Recorded here for review; do not
hand-edit in `st02`.

```
https://doi.org/10.3390/rs13051043
```

#### Additional citations (optional)

None. This limb cites only the original paper it confirms.

*(skip — optional)*

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 06.

This completes the turbidity limb of the FORRT chain. The chlorophyll-a limb
carries its own separate CiTO citation.
