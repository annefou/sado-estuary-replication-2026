# Published nanopub chain — URI registry

This replication published **two atomic FORRT chains that share one Quote**, composed by a **Research Synthesis**. Published on the Science Live network; view any nanopub via `https://platform-dev.sciencelive4all.org/np/?uri=<URI>`.

- **Original paper:** [10.3390/rs13051043](https://doi.org/10.3390/rs13051043) (Sent et al. 2021)
- **Shared Quote** (published once, reused by both chains): `https://w3id.org/sciencelive/np/RAXx0A9g5UJ5AM686y-9FOn5bwEdmb45xqhgVoNkCo3Pc`
- **Constellation entry point** (walks the whole graph): the Chl-a Outcome (Chain 1, step 05).

## Chain 1 — Chlorophyll-a limb · verdict **PartiallySupported → `qualifies`** (R² ≈ 0.10)

| Step | Template | URI |
|---|---|---|
| 01 | Quote-with-comment | https://w3id.org/sciencelive/np/RAXx0A9g5UJ5AM686y-9FOn5bwEdmb45xqhgVoNkCo3Pc |
| 02 | AIDA Sentence | https://w3id.org/sciencelive/np/RAbH8eTEXr3R85Nt4ZVoO2CTzJmbgPn3VFa21_ZulM5FE |
| 03 | FORRT Claim | https://w3id.org/sciencelive/np/RAuzyXFNXL_jqMA3b5isvsSW3W-LNjqGrMaeKdCW_VLWc |
| 04 | FORRT Replication Study | https://w3id.org/sciencelive/np/RAlQ4qJBnhxePAPzuL0Iy1mp4Ks61AAMfQCoP0kZ65ECM |
| 05 | FORRT Replication Outcome | https://w3id.org/sciencelive/np/RAoh82dxkJvR73OU_ttKf2_mtwgXY5_8qgcp3S7tmhcVM |
| 06 | CiTO Citation (`qualifies`) | https://w3id.org/sciencelive/np/RAPHEeNvUozDX7Am5yJm5T3SsIJPMLFCp4jmNY1YPGsq8 |

## Chain 2 — Turbidity limb · verdict **Validated → `confirms`** (R² ≈ 0.92)

| Step | Template | URI |
|---|---|---|
| 01 | Quote-with-comment | _shared — same as Chain 1 (`…qhgVoNkCo3Pc`)_ |
| 02 | AIDA Sentence | https://w3id.org/sciencelive/np/RAi5AIgx0JUM8WwqivSR7qUXne4wy3_MjJ3e26U5AhlAU |
| 03 | FORRT Claim | https://w3id.org/sciencelive/np/RA9BeRdRHcUCwth2RWceokYNHF403kh_f9pzVW0S01IVM |
| 04 | FORRT Replication Study | https://w3id.org/sciencelive/np/RAnwDtIlAWIqvXpldc4jr_BhZF10mbn1nSMjcBFieDfy4 |
| 05 | FORRT Replication Outcome | https://w3id.org/sciencelive/np/RAGe9U1qrzbrHI6bZjkM7d3vuwbAkv5j1K0S5cEC8HYkk |
| 06 | CiTO Citation (`confirms`) | https://w3id.org/sciencelive/np/RAeig8Es10GXSl0AF2-7Y-yncEG-QS4_fLd2lQTIgRhPI |

## Research Synthesis — composes both Outcomes into the parameter-asymmetry finding

| Step | Template | URI |
|---|---|---|
| 08 | Research Synthesis | https://w3id.org/sciencelive/np/RAFOMMXsXiYG-lWxSyjomq6wkhjx4t_BLo01u7Buuif2s |

Sources: Chain 1 Outcome (`qualifies`) **+** Chain 2 Outcome (`confirms`). Step 07 (Research Software) was intentionally not published.

## Format

URIs from Science Live are of the form `https://w3id.org/sciencelive/np/RA…`. The bare resolver form `https://w3id.org/np/RA…` returns the signed TriG directly (the `sciencelive/np` form redirects to the HTML viewer). Both identify the same nanopub.

## Cross-references

- Drafts: `nanopubs/drafts/` (Chl-a limb) and `nanopubs/drafts-turbidity/` (turbidity limb + synthesis)
- Chain-draft files the wizard consumed: `nanopubs/chain-draft.json`, `nanopubs/chain-draft-turbidity.json`
- Form structure: `docs/forrt-form-fields.md`
