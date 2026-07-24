# Draft: redistribution request to Hygeos

Send whenever convenient — **the pipeline does not depend on the answer.** The public image
ships without Polymer and reproduces the headline Chl-a analysis end-to-end; a "yes" here
would only add the atmospheric-correction intercomparison to the turnkey path.

European summer means a reply may take weeks. Do not block Phase 2, 3 or 4 on it, and do not
ship a Polymer-bearing public image before written consent is actually in hand — Terms of Use
§10 is explicit that consent must be *prior* and *written*.

Contact: via <https://hygeos.com/en/polymer/> or the support forum at
<https://forum.hygeos.com>.

---

**Subject:** Permission to include Polymer in a public, non-commercial replication container

Dear Hygeos team,

I am preparing an open replication study of Sent et al. (2021), *Deriving Water Quality
Parameters Using Sentinel-2 Imagery: A Case Study in the Sado Estuary, Portugal*
(doi:10.3390/rs13051043), which compared Acolite, C2RCC and Polymer for Sentinel-2 MSI
water-quality retrieval. Our replication applies the same processing chains to the
Westerschelde using open Rijkswaterstaat in situ data, and will be archived on Zenodo with a
citable DOI and published as a FORRT nanopublication chain.

The work is non-commercial scientific research, and I have read and accept the Polymer Terms
of Use (version 2.0). We use Polymer v4.17.3, unmodified.

For reproducibility we publish a Docker image so that others can re-run the analysis exactly.
Terms of Use §2 and §10 prevent us from including Polymer in that image, since publishing it
would constitute transfer to third parties. We therefore currently ship the image with
Acolite and C2RCC only, and Polymer is installed separately by each user from your
repository, under their own acceptance of the Terms.

§10 allows disclosure with your prior written consent, so I would like to ask whether you
would grant permission to include Polymer v4.17.3 inside a **public, non-commercial,
research-only container image** published for this replication. If it helps, we are glad to:

- restrict the image to a named, versioned release tied to this study;
- reproduce your copyright and proprietary notices, and ship `LICENCE.TXT` unmodified in the
  image;
- display the Terms of Use on container start and require explicit acceptance;
- state clearly in the image metadata and documentation that Polymer is licensed by Hygeos
  for non-commercial use and is not covered by the repository's own licence;
- cite Polymer and the appropriate reference in all outputs.

If a public image is not acceptable, we will keep the current arrangement — it works, and the
replication's headline result does not depend on the Polymer chain.

Thank you for making Polymer available for research use.

With best regards,

Anne Fouilloux
LifeWatch ERIC
ORCID 0000-0002-1784-2920
anne.fouilloux@lifewatch.eu
