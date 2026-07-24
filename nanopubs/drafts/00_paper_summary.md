# Paper summary

> This is a working scratchpad for the paper-analysis phase. The output of this file feeds the Quote / AIDA / Claim drafts. It is not itself a nanopub.

**Reference paper:** Deriving Water Quality Parameters Using Sentinel-2 Imagery: A Case Study in the Sado Estuary, Portugal

**DOI:** 10.3390/rs13051043

**Authors:** Giulia Sent, Beatriz Biguino, Luciane Favareto, Joana Cruz, Carolina Sá, Ana Inés Dogliotti, Carla Palma, Vanda Brotas, Ana C. Brito

**Year:** 2021 (Remote Sensing 13(5):1043; received 4 Feb 2021, accepted 2 Mar 2021, published 9 Mar 2021; CC BY 4.0)

**Local PDF:** `paper/sent-2021.pdf` (27 pages, md5 `4effe616d9e054710712cf17797b26de`)

## Headline claim

The paper's central empirical assertion is that Sentinel-2 MSI can retrieve the four
water-quality parameters in the Sado estuary with *parameter-dependent* accuracy — strong
for turbidity, weak for chlorophyll-a. That asymmetry is the testable content, and it is
what the replication should target.

Candidate quote sentence (Section 5, Conclusions, p. 24 — verified verbatim against the
PDF text layer, see `01_quote.md` for the normalisation notes):

> The turbidity product showed high consistency with in situ observations, proving the
> great capabilities of the MSI sensor to monitor this important water quality parameter.
> However, for the key parameter Chl-a further research is needed, with a more complete
> set of match-ups.

This is preferred over the Abstract's framing sentence ("Results suggest that Sentinel-2 is
useful for monitoring these parameters…") because it is *specific and falsifiable*: it names
which parameter succeeds, which fails, and in which direction.

## Methodology summary

- **Data sources:** Sentinel-2 A/B MSI **Level-1C** granules over the Sado estuary
  (Setúbal, Portugal; 212.4 km², WFD typology A2 mesotidal well-mixed), acquired
  **March 2018 – March 2020**, downloaded from the Copernicus Sentinel Scientific Data Hub
  (`scihub.copernicus.eu`, accessed 26 Nov 2020). In situ: **8 sampling stations**
  (#6–#8 outer area A, #1–#5 inner area B), monthly campaigns **March 2018 – November 2019**
  under the AQUASado project, sampled at high water to coincide with the S2 overpass.
- **Processing chain:** three atmospheric-correction processors compared —
  **Acolite v20190326**, **C2RCC v2.0**, **Polymer v4.12** — each at default settings, each
  crossed with a set of published bio-optical algorithms (7 for aCDOM, 4 for Chl-a, 3 for
  SPM, 2 for turbidity). Images resampled to 10 m; a **3×3 pixel** window centred on each
  station; match-up time window **±2 h**; IdePix v2.2 for pixel classification plus
  processor-specific quality flags.
- **Statistical model:** no inferential model — this is a **match-up validation and
  algorithm-intercomparison** design. Agreement metrics: R², slope, intercept, RMSE, BIAS,
  URMS, APD, RPD, summarised in Taylor and Target diagrams. Chl-a statistics in log scale;
  RPD/APD computed without log-transform.
- **Sample sizes:** **N = 19–21 match-ups** per algorithm/processor combination (Table 4);
  ternary-plot absorption characterisation N = 33. Small N is the single most important
  caveat on every reported R².
- **Headline numerical results** (Table 4 + Section 3.2, the numbers a replication compares
  against). Best chain per parameter, all with **AC-C2RCC** selected for the time series:

  | Parameter | Best chain | R² | APD | N |
  |---|---|---|---|---|
  | Turbidity | AC-C2RCC + Nechad 783 nm (`cN783`) | **0.84** | 33 % | 21 |
  | aCDOM (443 nm) | Polymer + TS443 (`pTS443`) — best overall; AC-C2RCC + TS443 used for time series | 0.608 (P) / 0.471 (C2RCC) | 46.6 % / 63.6 % | 21 |
  | Chlorophyll-a | AC-C2RCC + Gons et al. 2005 (`cGS`) | **0.63** | — (time-series mean APD **391 %**) | — |
  | SPM | Polymer + Nechad 705 nm (`pN705`); AC-C2RCC + Nechad 740 nm (`cN740`) used for time series | 0.57 (P) / 0.49 (C2RCC) | 26 % / 31 % | — |

  Processor-level bias: mean BIAS Acolite **2.78**, C2RCC **0.04**, Polymer **−0.07**;
  mean APD Acolite **254 %**. Acolite is the clear loser.

  Time-series chains selected: `cT443` (aCDOM), `cGS` (Chl-a), `cN740` (SPM), `cN783`
  (turbidity). Seasonal result: highest aCDOM, Chl-a, SPM and turbidity in **Spring and
  Summer**, concentrated in inner region B.

## Replication design choice

- [ ] **Reproduction Study** — direct reproduction: same methodology, same tools.
- [x] **Replication Study** — replication with different methodology or conditions.
- [ ] **Reproduction/Replication Study** — both.

**Justification.** A Reproduction Study is *not achievable* here, and the blocker is
explicit in the paper. The Data Availability Statement (p. 25) reads:

> Data Availability Statement: The data presented in this study are available on request from the
> corresponding author.

The in situ match-up dataset — the 8-station aCDOM / Chl-a / SPM / turbidity measurements
that every R², RMSE and APD in Table 4 is computed against — is therefore **not openly
available**. Without it the validation statistics cannot be recomputed, only re-derived
against a different reference dataset.

What *is* openly reproducible is the satellite half of the pipeline: Sentinel-2 L1C is
free from the Copernicus Data Space Ecosystem, and all three AC processors and every
bio-optical algorithm in Table 2 are published with their coefficients. That is a change of
data source with the method held constant, which is a Replication Study, not a Reproduction.

**Site and period (frozen 2026-07-23): the Westerschelde, January 2016 – July 2026.** The
source scan (`00b_in_situ_source_scan.md`) established that no open in situ reference exists
for the Sado in any period, so the replication moves to the estuary where data does exist:
the Westerschelde, a mesotidal, well-mixed, turbid estuary in a LifeWatch ERIC member state,
with six Rijkswaterstaat axis stations.

The period deliberately does **not** match the original study's March 2018 – March 2020 field
campaign. At that window the replication produced only 13–16 chlorophyll match-ups —
comparable to the paper's own N = 19–21 — because Rijkswaterstaat samples the whole estuary
on shared cruise days and every station falls in the same two MGRS tiles, so adding stations
adds observations on the same dates against the same scenes. Extending to the full
Sentinel-2 era is what actually buys statistical power.

Realised match-ups (±2 h, footprint-verified, from executing `01` and `02`): **Chl-a 53,
SPM 61, Secchi 59, phaeophytin 47, turbidity 15**, against 1382 Sentinel-2 L1C scenes.
aCDOM has no open equivalent and is declared untested. These are an upper bound —
per-pixel quality screening in `03` reduces them further.

Two open decisions, flagged rather than assumed (see "Notes" below): which independent
in situ source to validate against, and whether to request the original AQUASado data
from the corresponding author.

**Update (2026-07-22) — the first decision has been scanned, see `00b_in_situ_source_scan.md`.**
There is **no open, contemporaneous, in-estuary in situ dataset** for the Sado over
March 2018 – March 2020. GLORIA has zero Portuguese records; EMODnet Chemistry has one
October 2018 shelf cruise sampled at night, yielding zero possible match-ups; EEA Waterbase
registers 19 transitional-water stations inside the estuary but Portugal reports no
transitional-water chemistry at all; the Copernicus Marine in situ IBI product begins
2020-01-01. SNIRH could not be reached (HTTP 403 from this host) and is the one source still
to be checked by hand. The Replication-not-Reproduction choice therefore stands on firmer
ground than written above — the blocker is not just that the original data are request-only,
but that no open substitute exists. Three surviving designs are set out at the end of the
scan note; the design choice is not yet frozen.

## Notes for downstream drafts

- **The Quote must carry the asymmetry.** The paper's own abstract hedges ("useful …
  however, with challenges … such as Chl-a"). The Conclusions sentence is sharper and is
  the better anchor. Whatever is chosen, the AIDA sentence must stay **atomic** — "turbidity
  is retrieved accurately" and "Chl-a is not" are *two* empirical findings. Per `CLAUDE.md`
  § Atomic AIDA, that means either two AIDA nanopubs on two Claims, or picking one.
  ~~The turbidity limb (R² = 0.84) is the stronger, more citable single claim.~~
  **Superseded 2026-07-22:** the anchor is the **Chl-a** limb. The Westerschelde has no open
  turbidity for 2018–2020, and the Chl-a limb's closing clause ("with a more complete set of
  match-ups") is exactly what 274 match-ups supply. See `00b_in_situ_source_scan.md`
  § DESIGN FROZEN.
- **PDF hazard — duplicated text layer.** This PDF embeds a leftover
  *"Remote Sens. 2021, 13, x FOR PEER REVIEW … of 30"* layer alongside the published text,
  so many passages appear **twice** in extraction, with different line breaks and hyphenation.
  A verbatim quote lifted from the wrong copy would be a peer-review-draft variant, not the
  published sentence. Always confirm which block a candidate quote came from.
- **Extraction artifacts** (counted across 111k chars): 138 ligature codepoints
  (`ﬁ` U+FB01, `ﬂ` U+FB02 — *not* ASCII `fi`/`fl`), 97 hyphen-linebreaks, 14 spurious
  intra-word spaces (`Chl- a`, `V .`). Normalise before quoting; see `01_quote.md`.
- **Small N.** Every headline R² rests on N ≈ 19–21. The replication should not over-read a
  difference in R² as a contradiction; characterise honestly per `DOMAIN.md`
  § Honest negative results.
- **Typo in source** (p. 15): "The best performing processing chain of *eaxh* parameter" —
  quote around it, or use `[sic]`.
- **No GBIF involvement**, so `DOMAIN.md` § GBIF download DOIs does not apply. The citable
  data identifiers here are Copernicus product IDs plus whatever in situ source is chosen.
