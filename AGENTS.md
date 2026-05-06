# autoJobapp

Multi-source CS/IT job scraper for US positions. No framework — two standalone Python scripts.

## Scripts

- `job_scraper.py` — Uses JSearch API (RapidAPI). Requires `JSEARCH_API_KEY` env var. Original script, focuses on entry-level roles.
- `cs_it_job_scraper.py` — Free sources, no API key needed. Primary script. Searches Remotive, USAJOBS, YC Work at a Startup, and a fallback tech jobs API.

## Setup

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python cs_it_job_scraper.py          # primary (free sources, US-only)
python job_scraper.py                 # requires JSearch API key
```

## Known API issues

- **Wellfound (wellfound.com)** — Blocked by DataDome anti-bot (403). Cannot scrape directly. Do not attempt.
- **USAJOBS** — Returns 401 without an API key. Get one free at https://developer.usajobs.gov/ then `export USAJOBS_API_KEY='key'`
- **Indeed RSS** — Deprecated endpoint (404). Removed from script.

## Architecture

Both scripts follow the same pattern:
1. Search multiple sources → append to `self.jobs` list
2. `filter_us_only()` — US location filter (state codes + US indicators)
3. `remove_duplicates()` — dedup by lowercase `title|company` key
4. `save_to_file()` — appends to `jobs.json` (note: uses `'a'` mode, accumulates across runs)

`cs_it_job_scraper.py` sources and their URL patterns:
- Remotive: `GET /api/remote-jobs?search={query}` (no key, filters US in-code)
- USAJOBS: `GET /api/search?Keyword={q}&Country=US` (needs `Authorization-Key` header)
- YC Startups: `GET /jobs/role/{role-slug}` (scrapes HTML, server-side rendered)
- TechJobs fallback: `GET /jobs?q={q}&location=US` on pythonprogramming.herokuapp.com

## Conventions

- Output: `jobs.json` (append mode — file grows across runs)
- All search queries are hardcoded in `search_all_cs_it_jobs()` method
- 1s rate limit between API calls; 30s backoff on 429 (JSearch only)
- `User-Agent` is Chrome browser string to avoid basic bot detection
