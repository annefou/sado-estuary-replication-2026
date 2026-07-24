# In situ reference source scan — Sado estuary, March 2018 – March 2020

> Working scratchpad for the paper-analysis phase, feeding the "Replication design choice"
> section of `00_paper_summary.md`. Not itself a nanopub.
>
> **Question:** does an open, contemporaneous, in-estuary in situ dataset exist that could
> serve as an independent validation reference for Sentinel-2 retrievals of turbidity,
> Chl-a, SPM and aCDOM in the Sado estuary over the paper's study period?
>
> **Answer: no.** Every candidate was checked against its own API or archive. Results below.

**Scan date:** 2026-07-22.
**Target window:** lon −9.15 … −8.30, lat 38.30 … 38.75 (Sado estuary + mouth + adjacent shelf).
**Target period:** 2018-03-01 … 2020-03-31.
**Target parameters:** turbidity, Chl-a, SPM/TSS, aCDOM(443).

## Summary table

| Source | In-estuary records 2018–2020 | Verdict | Basis |
|---|---|---|---|
| GLORIA (PANGAEA 10.1594/PANGAEA.948492) | **0** | Ruled out | 0 of 7572 records in Portugal; 0 in the 38–39 N / 9.5–8 W window |
| EMODnet Chemistry (Eutrophication Atlantic) | **0 usable** | Ruled out | 23 records, but offshore, October 2018 only, night-time |
| EEA Waterbase — Water Quality ICM 2026 | **0** | Ruled out | PT reports only rivers + lakes, nothing after 2014 |
| Copernicus Marine in situ IBI NRT (013_033) | n/a | Ruled out | Product record starts 2020-01-01 |
| SNIRH / APA | **no turbidity variable** | Ruled out for turbidity | Checked by hand by A. Fouilloux, 2026-07-22 |
| AQUASado original match-ups | n/a | Request-only | Data Availability Statement, p. 25 |

## Per-source detail

### GLORIA — ruled out

The global hyperspectral in situ dataset for optical water-quality sensing (7572 records,
450 water bodies, CC-BY-4.0). Downloaded and queried `GLORIA_meta_and_lab.csv` directly:

- Records with `Country` containing "Portugal": **0**.
- Records in 38.0–39.0 N, −9.5 … −8.0 W (Sado + Tagus): **0**.
- Records in the broad Iberian Atlantic (36–44 N, −10 … −6): 38, all Spanish.

Scientifically the closest match on *parameters* (it carries Rrs + Chl-a + TSS + aCDOM440
together, which is exactly the paper's variable set) and the furthest on *geography*.

### EMODnet Chemistry — ruled out

Queried the ERDDAP endpoint `erddap.emodnet-chemistry.eu`. Of 44 datasets, 8 have bounding
boxes covering the Sado; `EUT_ATLANTIC_PROFILES` is the only one carrying both
`Water_body_chlorophyll_a` and `TURBXXXX`. In the target window it returns 75 records
across all time, of which 23 fall in 2018 and none in 2019 or 2020.

Those 23 records fail on three independent grounds:

1. **Outside the estuary.** They sit at 38.31–38.40 N, −8.83 … −9.04 W — the shelf south
   and west of the estuary mouth, not the 212 km² estuarine body the paper maps. The
   paper's inner region B, where the seasonal signal is concentrated, is not sampled at all.
2. **Single cruise, single month.** All 23 belong to `IHPT-AQUIMAR2018-2` (Instituto
   Hidrográfico), 14–16 October 2018. No seasonal cycle, no inter-annual signal.
3. **Night-time.** Sampling timestamps are 15:15, 16:35, 18:02, 19:32, 22:56 and 00:38 UTC.
   Sentinel-2 overpasses the Sado around 11:00–11:30 UTC. Under the paper's ±2 h match-up
   rule, **not one of these records yields a match-up**, and no relaxation of the window
   short of ±12 h would change that.

No SPM/TSS and no aCDOM in the dataset regardless.

### EEA Waterbase — ruled out (but see below)

This was the strongest a-priori candidate: Waterbase — Water Quality ICM (1900–2025) is the
European aggregation of exactly the national WFD monitoring that SNIRH holds, and its
spatial registry **does** contain the Sado estuary. Queried
`WISE6_SpatialObjects_DerivedData`: 35 Portuguese sites in the window, of which **19 are
transitional-water sites inside the estuary**, mapped to water bodies SADO-WB1 … WB6 — the
same WFD water bodies the companion paper (Santos et al. 2022) samples. Named sites include
`PT22D03S` SADO – BOCA ESTUARIO (38.5025, −8.90613, the mouth), `PT22D02S` CAIS PIRITES–CAIS
SAPEC, `PT23D02S` TROIA INTERIOR, `PT22E01S` CANAL AGUAS MOURA, `PT23E02S` CANAL COMPORTA,
plus `PTESD101/102/201`.

The stations exist; **the measurements do not.** Scanning all 6 450 192 rows of
`WISE6_AggregatedData` for those site identifiers returns **0 rows**. Portugal's entire
contribution is 3387 river rows + 1922 lake rows, none from 2015 onwards; there is no
transitional- or coastal-water chemistry at all. The by-water-body aggregation has 0 PT rows.

So Waterbase gives us **station geometry we can reuse** (useful for placing the 3×3 window
and for naming water bodies in the Study draft) but no observations.

### Copernicus Marine in situ — ruled out on period

`INSITU_IBI_PHYBGCWAV_DISCRETE_MYNRT_013_033` STAC record gives a temporal interval starting
**2020-01-01**, leaving at most a three-month overlap with the paper's window, and the
product is coastal/shelf-oriented rather than estuarine.

### SNIRH — resolved by hand: no turbidity

`snirh.apambiente.pt` returns **HTTP 403** to every request from this machine (plain curl,
browser User-Agent, and the fetch tool alike — an nginx block, not a login wall), so it could
not be verified programmatically.

**Checked manually by A. Fouilloux on 2026-07-22: SNIRH does not expose a turbidity
variable.** This confirms the indirect evidence from the paper itself — Sent et al. cite
SNIRH exactly once, on p. 4, and only for **wind**: *"hourly average with a maximum of
~8 m/s in 2018 and ~6m/s in 2019, Source: https://snirh.apambiente.pt (accessed on
26 November 2020)"*. A group running a monthly in-estuary campaign for two years, already
using the portal, did not draw water-quality data from it.

Still open, and narrower: whether SNIRH carries **Sólidos Suspensos Totais** (SPM) or
**Clorofila a** for the Sado transitional-water stations over 2018–2020. Those are two of the
paper's four parameters, so a positive answer would make SNIRH partially usable even though
the turbidity limb is dead.

## Consequence for the design choice

The Replication-not-Reproduction choice already recorded in `00_paper_summary.md` stands, and
for a stronger reason than originally written. The blocker is not only that the original
AQUASado match-ups are request-only — it is that **no open substitute exists**. The
originally-imagined design ("re-run the chain, validate against an independent in situ
reference") has no in situ reference to validate against.

Three designs survive. All are honest replications; they differ in what they can conclude.

1. **Satellite-vs-satellite (no in situ).** Test the paper's *relative* claims — turbidity
   retrieved consistently, Chl-a not; Acolite biased high — by re-running the three AC
   processors and the Table 2 algorithms over the same scenes and comparing against
   Sentinel-3 OLCI operational products (`OCEANCOLOUR_ATL_BGC_L3_MY_009_113`, verified to
   cover 1997–2026). Fully open and fully reproducible. Cannot reproduce an absolute R²
   against ground truth; can test processor-level consistency and the turbidity/Chl-a
   asymmetry.
2. **Same method, different estuary.** Port the pipeline to an estuary with dense open in
   situ (continuous turbidity + Chl-a at sub-hourly resolution). Tests whether the paper's
   asymmetry generalises, and escapes the N ≈ 19–21 limitation that the paper itself flags.
   Changes the geographic scope of the claim.
3. **Request AQUASado and reproduce.** Timeline depends on the corresponding author.

Option 1 stays closest to the original claim; option 2 gives far more statistical power;
option 3 is the only route to a true Reproduction.

## Second scan — European candidate sites (2026-07-22)

Following the Sado result, the site is now selected **by data availability**, constrained to
Europe and preferably a LifeWatch ERIC member state. The Scheldt / Westerschelde was scanned
first: it is the closest typological analogue to the Sado (mesotidal, well-mixed, turbid,
resuspension-dominated, strong inner→outer gradient) and it straddles the Netherlands and
Belgium, both LifeWatch ERIC members.

### Westerschelde (NL) — verified, and the recommended site

Source: Rijkswaterstaat DDAPI 2.0, `https://ddapi20-waterwebservices.rijkswaterstaat.nl`.
Open, no API key required. (The legacy `waterwebservices.rijkswaterstaat.nl` host is being
decommissioned end of April 2026 — use the new base URL.)

Catalogue: **56 monitoring sites** in the Westerschelde window (3.35–4.35 E, 51.30–51.58 N),
of which 17 list turbidity, 55 chlorophyll and 22 suspended matter. Stations run the full
estuary axis from Vlissingen at the mouth to Schaar van Ouden Doel at the Belgian border —
the same inner/outer structure the Sado paper uses.

**Catalogue capability was then checked against actual observations** (the trap Waterbase
set), for March 2018 – March 2020, at six axis stations:

| Quantity | Code | Returned | **Usable** | Verdict |
|---|---|---|---|---|
| Chlorophyll-a | `CONCTTE` / `CHLFa`, µg/l | 274 | **217** | Usable |
| Suspended matter (SPM) | `CONCTTE` / `OS`, mg/l | 274 | **240** | Usable, co-located with Chl-a |
| Phaeophytin-a | `CONCTTE` / `FEOa`, µg/l | 219 | **164** | Bonus — constrains Chl-a algorithm error |
| Secchi depth | `ZICHT`, dm | 238 | **232** | Usable (transparency proxy) |
| Turbidity | `TROEBHD` | 0 | 0 | Absent in this period |
| Light extinction | `EXTINCTE` | 0 | 0 | Absent at these stations |

> **Corrected 2026-07-22 after executing `notebooks/01_data_download.py`.** The "Returned"
> column is what the API hands back and is what an earlier revision of this note reported.
> **152 of those 1005 observations are Rijkswaterstaat's missing-data marker, the literal
> number `999999999999`** — not a null. It survives `dropna()`, and left in place it inflated
> the chlorophyll mean to 2×10¹¹ µg/l. The "Usable" column is post-screening and is the count
> to quote. Screened values are plausible: Chl-a mean 5.3 µg/l (range 0.53–26), SPM mean
> 48.9 mg/l (range 1–360) — appropriate for a turbid mesotidal estuary.
>
> The marker is not evenly spread: `soelekerkepolder.oost` alone accounts for 38 of the
> chlorophyll gaps and 33 of the SPM gaps, so that station is roughly half empty and needs
> care in station-level interpretation.

**Note on the SPM code.** Rijkswaterstaat files suspended matter as parameter `OS`
("Onopgeloste stoffen", undissolved solids), **not** under any label containing *zwevende
stof* — that phrase is reserved for contaminants measured *in* the suspended-matter phase
(`MASSFTE`, mg/kg). A search on the obvious Dutch term returns nothing and wrongly suggests
SPM is absent. The parameter enumeration under `CONCTTE` (203 distinct parameters at
Hansweert) is the reliable way to find it.

SPM lands on exactly the same 274 sampling occasions as Chl-a, so **two of the paper's four
parameters** are testable here, from co-located samples, with no extra field effort.

Two properties make the chlorophyll records genuinely usable rather than merely present:

- **Timestamps are recorded**, not just dates. A large share fall in the 09:00–13:00 window,
  bracketing the Sentinel-2 overpass, so the paper's ±2 h match-up rule can be applied
  as-written rather than relaxed.
- **~274 candidate samples against the paper's N = 19–21.** Roughly an order of magnitude
  more, at six stations, before the other ~50 Westerschelde sites are even considered.

Turbidity does appear at these stations from around 2024 (≈5 records per station-quarter), so
a turbidity-bearing design is possible if the period moves to 2024+.

### Other European candidates checked

- **Belgian Part of the North Sea** (LifeWatch Belgium / VLIZ observatory area) — EMODnet
  Chemistry returns 128 records in 2018, **943 in 2019, 605 in 2020**. Dense, and in a
  well-studied turbid Case-2 water body. Chlorophyll only in that dataset — no turbidity.
- **Oosterschelde** — 35 sites, 18 listing turbidity, 27 suspended matter. Not yet
  observation-checked; the obvious second stop if the Westerschelde design needs turbidity.
- **Wadden Sea / Ems-Dollard** — 69 and 24 sites; EMODnet returns almost nothing after 2018
  for Ems-Dollard.

### Consequence for the chain anchor

`01_quote.md` quotes both limbs of the paper's asymmetry, but the AIDA must be atomic, and
the plan recorded in `00_paper_summary.md` § Notes was to anchor on the **turbidity** limb as
the stronger, more citable claim. The Westerschelde data does not support that limb for
2018–2020.

This is not a problem so much as a redirection, and arguably a better one. The second
sentence of the quote reads: *"However, for the key parameter Chl-a further research is
needed, with a more complete set of match-ups."* A replication carrying ~274 Chl-a match-ups
against the original ~20 **is** the more complete set of match-ups the authors asked for. The
already-verified verbatim quote supports this anchoring unchanged.

Three ways forward were put to the user, in preference order:

1. **Westerschelde, anchor on the Chl-a limb, keep the 2018–2020 period.** Answers the
   paper's own stated call. Turbidity limb left untested and declared as such.
2. **Westerschelde, move the period to 2024+.** Recovers turbidity, loses the exact-period
   correspondence with the original study.
3. **Add the Oosterschelde or the Belgian coastal zone** as a second site to recover the
   turbidity limb alongside the Westerschelde Chl-a limb.

## PERIOD UNFROZEN — 2026-07-23

The 2018–2020 window was abandoned after `02_data_clean.py` measured the realised match-up
count. **At the original window the replication yielded 13 chlorophyll match-ups from six
stations and 16 from twelve — comparable to the paper's own N = 19–21, not an improvement on
it.** The design's premise ("a more complete set of match-ups") was false as specified.

Adding stations does not fix it, and the reason is structural: Rijkswaterstaat samples the
whole estuary **on the same cruise days**, and every Westerschelde station falls in the same
two MGRS tiles (`T31UES`, `T31UET`). Extra stations therefore contribute observations on the
*same dates* against the *same scenes*. 741 observations across 12 stations still produced
only 16 match-ups. **Only more dates help.**

The original window was set by the authors' field campaign, not by the science, and this
replication already departs from the paper on site — so period correspondence was never
load-bearing.

## DESIGN FROZEN (revision 2) — 2026-07-23

| | |
|---|---|
| **Type** | Replication Study (different site, different period, different in situ reference; method held constant) |
| **Site** | Westerschelde, Netherlands — mesotidal, well-mixed, turbid; LifeWatch ERIC member state |
| **Stations** | 6 estuary-axis stations, Vlissingen (mouth) → Schaar van Ouden Doel (Belgian border) |
| **Period** | **January 2016 – July 2026** — the full Sentinel-2 era |
| **In situ reference** | Rijkswaterstaat DDAPI 2.0, open, no API key |
| **Sentinel-2 scenes** | **1382** L1C scenes intersecting the estuary, cloud cover < 60 % |
| **Chain anchor** | The **Chl-a** limb — now settled on evidence, see below |
| **Not tested** | aCDOM — no open equivalent at this site in any period; declare in the Outcome's limitations |

### Realised match-ups (±2 h, footprint-verified), from `02_data_clean.py`

| Quantity | Usable observations | **Matched** |
|---|---|---|
| Chlorophyll-a | 1154 | **53** |
| SPM | 1236 | **61** |
| Secchi depth | 1154 | **59** |
| Phaeophytin-a | 892 | **47** |
| Turbidity | 279 | **15** |

Match rate is ~5 % throughout, set by cloud-free Sentinel-2 revisit against roughly monthly
sampling. These remain an **upper bound** — per-pixel quality screening in `03` will reduce
them further.

### What the N comparison does and does not mean — READ BEFORE DRAFTING

Earlier revisions of this note described 53 Chl-a match-ups as "~2.5× better" than the
original study's 19–21. **That framing is wrong and must not reach the chain.** We are in a
different estuary over a different decade; the two counts are not measuring the same thing.

| The comparison **is** valid for | The comparison is **not** valid for |
|---|---|
| Stating how well *our own* Westerschelde estimate is constrained | Claiming our result supersedes or corrects theirs |
| Justifying which limb we anchor on, since it is the limb we can estimate most precisely | Claiming we supplied "the more complete set of match-ups" the paper asked for |
| Reporting our own statistical power honestly in the Outcome | Any statement about Chl-a retrieval **in the Sado** |

The decisive point: the quoted sentence asks for a more complete set of match-ups **for the
Sado**. Our 53 Westerschelde match-ups do not answer that call — they answer a *generalised*
version of it. Nobody can answer the literal call with open data, which is the whole reason
the site moved. Saying otherwise would be an overclaim, and the paper's authors would be
right to object.

**A second confound, from the period.** The original N = 19–21 spans ~1.5 years; our 53 spans
10.5 years. A decade of match-ups samples far more environmental variance — nutrient-policy
change in the Scheldt, shifting phytoplankton community composition, S2A-only versus
S2A+S2B, and successive processing baselines. A lower R² over ten years does **not**
necessarily mean worse retrieval than a higher R² over eighteen months; it can simply mean a
wider range of conditions was sampled. Pooling a decade into a single agreement statistic is
itself a deviation from the original method and must be declared.

**Mitigation — stratify.** `03_analysis.py` should report the Chl-a agreement statistics
twice: once over the full 2016–2026 period, and once over a **2018–2020 subset matching the
original window**. The subset will be underpowered (13–16 match-ups, comparable to the
paper's own N), but reporting both partially separates the *site* effect from the *period*
effect. Neither number alone can do that.

### The chain anchor is settled: Chl-a

Extending the period made turbidity available (Rijkswaterstaat turbidity at these stations
begins in 2024), which reopened the possibility of anchoring on the turbidity limb — the
paper's stronger, more citable claim. **The data says no.** Turbidity yields only 15
match-ups, *fewer* than the original study's 21, because it exists for barely 2.5 years.
Anchoring there would mean testing a well-supported claim with less evidence than the people
who made it — the opposite of what a replication is for.

Chlorophyll-a yields 53. Stated carefully — and per the section above, this is a claim about
*our* study, not a comparison of evidence bases — Chl-a is the limb whose Westerschelde
agreement statistic we can estimate most precisely, and it is the limb the original authors
themselves flagged as uncertain. Both make it the right thing to anchor an atomic claim on.

**Anchor: Chl-a.** Turbidity is still processed and reported as a secondary result, labelled
as resting on fewer match-ups than the original study had.

The claim under test is the second sentence of `01_quote.md`: that for Chl-a, further
research with a more complete set of match-ups is needed. This replication supplies that
set — roughly ten times the original N — and reports whether the paper's weak Chl-a
performance persists when sample size is no longer the binding constraint.

Honest framing required in the Outcome (`DOMAIN.md` § Honest negative results): a different
estuary is a different optical regime, so a divergent Chl-a result is evidence about
*generalisability*, not automatically evidence that the original analysis was wrong.

## Reproducing this scan

Queries were run against live APIs on the scan date. The GLORIA archive, the Waterbase
spatial + aggregated CSVs, and the ERDDAP JSON responses are not committed (≈2.5 GB
unpacked); re-fetch from the endpoints named above. The Waterbase share token is
`ZcJ37WK6oaWonFJ` on `https://sdi.eea.europa.eu/datashare/public.php/webdav/`.
