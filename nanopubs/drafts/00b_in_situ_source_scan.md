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

## Reproducing this scan

Queries were run against live APIs on the scan date. The GLORIA archive, the Waterbase
spatial + aggregated CSVs, and the ERDDAP JSON responses are not committed (≈2.5 GB
unpacked); re-fetch from the endpoints named above. The Waterbase share token is
`ZcJ37WK6oaWonFJ` on `https://sdi.eea.europa.eu/datashare/public.php/webdav/`.
