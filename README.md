# blazingstar-data

A small, unofficial demo of how to pull the **free public federal-budget data**
that [BlazingStar Analytics](https://www.blazingstaranalytics.com/) mirrors at
**[data.blazingstaranalytics.com](https://data.blazingstaranalytics.com/)**.

Everything served there is a mirror of primary federal sources (OMB MAX.gov,
GovInfo/GPO, the Federal Register, Regulations.gov), released under
[**CC0 1.0**](https://creativecommons.org/publicdomain/zero/1.0/) (public
domain). There is **no API key and no login** — each dataset is a single
`index.json` you can fetch with `requests` and load straight into pandas. (One
gotcha: the CDN returns 403 to requests that send no `User-Agent`, so set one —
the notebook does.) Every record carries its `source_url` and a pull timestamp;
the execution files also carry a published SHA-256 so you can byte-verify them
against OMB.

> This repo is not affiliated with or endorsed by BlazingStar Analytics. It just
> documents the public endpoints and shows them being used.

## Quick start

```bash
pip install -r requirements.txt
jupyter notebook demo.ipynb
```

Or open it in Colab (no install needed):

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/abigailhaddad/blazingstar-data/blob/main/demo.ipynb)

> The Colab badge points at `abigailhaddad/blazingstar-data` on GitHub `main`.
> It works once this repo is pushed there; adjust the URL if you fork or rename.

## The datasets

All endpoints are plain JSON over HTTPS unless noted. `{fy}` is a 4-digit
fiscal year.

| Dataset | Cadence | Index endpoint | What's in a row |
|---|---|---|---|
| **Apportionments (SF-132)** | nightly | `https://cdn.bzstr.co/sf132/fy{fy}/index.json` (FY2022–2026) | `tafs`, `agency`, `bureau`, `account_name`, `total_approved_amount`, `iteration`, `approval_timestamp`, `source_url`, `mirror_url`, `hash_sha256` |
| **SF-133 Execution** | monthly | `https://liatris.blazingstaranalytics.com/sf133/index.json` (+ crosswalk `https://cdn.bzstr.co/sf133/agency-index.json`) | per-agency monthly `.xlsx` (submitter-identity columns blanked), with `hash_public` / `hash_download` |
| **President's Budget Appendix** | annual | `https://cdn.bzstr.co/budget_appendix/{fy}/json/index.json` (FY2027) | 29 volumes → per-account Program & Financing, object-class, and employment lines |
| **Spend Plans** | as filed | `https://cdn.bzstr.co/spend-plans/index.json` | court-ordered agency spend-plan PDFs: `agency`, `bureau`, `fiscal_year`, `url`, `source_url` |
| **CFR Redlines** | daily | `https://cdn.bzstr.co/redlines/index.json` | consequential proposed rules: `title`, `agency`, `rin`, `comments_close_on`, `redline_url`, `source_url` |

The website also surfaces *Spending Constraints*, a *Most-Commented* docket
leaderboard, and a curated *Reference Library* (OMB Circulars, GAO Red Book,
Treasury Financial Manual, CRS) — those are page-level views over the same
mirrored sources.

## The join key: TAFS

The **Treasury Account Symbol (TAFS)** ties these together and out to
[USAspending](https://www.usaspending.gov/): an apportionment (SF-132) sets the
legal spending limit on a TAFS, the SF-133 reports execution against it, and
awards in USAspending draw down from it. That's the appropriation → apportionment
→ execution → award chain on a single identifier.

## What the notebook does

- **Access tour** — fetches every dataset into a pandas DataFrame, with each
  record's federal `source_url` carried alongside.
- **"What changed this week"** — apportionments update nightly and each account
  (TAFS) can be re-apportioned, so the notebook compares each account's latest
  `iteration` against the prior one and surfaces the dollar moves in the most
  recent 7 days (e.g. a $17.6B bump to DOE's Title 17 loan account), plus an
  agency-level rollup. The window is anchored to the latest approval in the
  file, so it stays meaningful whenever you run it.
- **Byte-level verification** — recomputes the published SHA-256 for an
  apportionment file and an SF-133 spreadsheet to confirm byte-equivalence with
  OMB.

### A note on sourcing

The data is CC0, so attribution isn't legally required — but every record
exposes a `source_url` to its authoritative federal origin (OMB MAX.gov,
GovInfo, the Federal Register), and the notebook surfaces it in every table.
When citing, lead with that primary source and note the BlazingStar mirror as
the access path; for apportionment/SF-133 figures you can also cite the
recomputed SHA-256 to assert byte-equivalence with OMB. See the closing "How to
cite" cell.

## Files

- `demo.ipynb` — the notebook described above.
- `requirements.txt` — `requests`, `pandas`, `openpyxl` (for the SF-133 Excel).

## License

The code in this repo is released into the public domain under
[CC0 1.0](LICENSE), matching the data it demonstrates. The data itself is CC0
from BlazingStar Analytics' mirror of federal sources; the underlying records
are U.S. Government works.
