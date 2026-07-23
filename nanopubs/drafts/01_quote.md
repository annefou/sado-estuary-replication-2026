# 01 — Quote-with-comment (paper-rooted chains)

> Run the pre-flight checklist in `docs/forrt-form-fields.md` § Pre-flight checklist before drafting.
>
> If this is a question-rooted chain, use `01_pico.md` or `01_pcc.md` instead — see `docs/chain-decision-tree.md`.
>
> **After choosing the chain shape, delete the two step-1 alternates you aren't using.** Once you've decided this chain is paper-rooted and keep `01_quote.md`, run:
> ```bash
> rm nanopubs/drafts/01_pico.md nanopubs/drafts/01_pcc.md
> ```

**Form heading:** *"Annotate a paper quotation — Annotating a paper quotation with personal interpretation"*

## Field-by-field draft

<!-- field: paper -->
### Cited DOI (text input, required)

Format: starts with `10.` — bare DOI, **NOT** `https://doi.org/...` form.

```
10.3390/rs13051043
```

### Quote mode (radio button)

- [x] **Quote whole text (less than 500 characters)**
- [ ] Quote start/end *(use this if the quote exceeds 500 chars)*

<!-- field: quotation -->
### The exact quotation from the paper (max. 500 characters) (textarea, required)

Verbatim from the paper PDF in `paper/`. Character-for-character. ≤ 500 chars in whole-text mode.

> _Read the PDF first. Don't paraphrase from memory. See `docs/verify-before-drafting.md`._

```
The turbidity product showed high consistency with in situ observations, proving the great capabilities of the MSI sensor to monitor this important water quality parameter. However, for the key parameter Chl-a further research is needed, with a more complete set of match-ups.
```

Character count: 276 / 500.

**Verification record.** Source: `paper/sent-2021.pdf` (md5 `4effe616d9e054710712cf17797b26de`),
Section 5 *Conclusions*, page 24 (footer reads `Remote Sens. 2021, 13, 1043 … 24 of 27`).
Text extracted with `pdftotext -layout`; the sentence pair occurs **exactly once** in the
extraction, so this is not the leftover peer-review text layer flagged in
`00_paper_summary.md` § Notes. Line-wrap hyphenation was absent in this passage; the only
normalisation applied was joining the extractor's line breaks into single spaces. All
characters are ASCII — no ligatures, no en-dashes, and `Chl-a` uses a plain ASCII hyphen.

<!-- field: quotation-end -->
### End of quotation (optional - use when quoting beginning and end of a longer passage, max. 500 characters) (textarea, optional)

Only when quoting the beginning *and* end of a longer passage — set the mode above to
**Quote start/end**, put the opening phrase under the previous heading and the closing
phrase here. Leave empty for a single short quote.

*(skip — optional; the quote is 276 chars, well within whole-text mode)*

```

```

<!-- field: comment -->
### Our interpretation and explanation of why this quotation is relevant (max. 800 characters) (textarea, required)

Why this quote matters and what the replication tests. Connect the paper's claim to the work this repo does. Don't repeat the quote.

```
The abstract hedges; this sentence does not. It commits to a parameter-dependent verdict, and that is what decides whether Sentinel-2 MSI is operationally usable under the Water Framework Directive: a sensor trustworthy for one variable but not another is a different monitoring proposition from one that simply works. That verdict rests on 19 to 21 match-ups from one estuary over two years. This replication answers the sentence's own closing call, re-running the processing chain over the Westerschelde — a comparably turbid, well-mixed mesotidal estuary — against 217 quality-screened in situ chlorophyll observations spanning the same 2018–2020 window, and tests whether the Chl-a verdict survives a more complete set of match-ups.
```

Character count: 736 / 800.

> **Wording is deliberate.** 217 is the count of *in situ observations* that survive
> Rijkswaterstaat's missing-data screening — **not** the final match-up count. A match-up
> additionally requires a cloud-free Sentinel-2 scene within ±2 h, so the realised N will be
> lower and is not known until Phase 3. Do not restate 217 as "217 match-ups" anywhere in the
> chain; the Outcome reports the realised figure.

> **Note on the anchor.** The quotation deliberately carries both limbs of the paper's
> asymmetry, but the AIDA that follows must be atomic, and it anchors on the **Chl-a** limb —
> the second sentence — not the turbidity limb. The reason is in
> `00b_in_situ_source_scan.md`: the Westerschelde has no open turbidity for 2018–2020, but it
> has 274 co-located Chl-a and SPM match-ups, which is precisely the "more complete set of
> match-ups" the quoted sentence asks for. The quotation itself is unchanged and stays
> verbatim.

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 01.
