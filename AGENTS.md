# AGENTS.md

This file points AI agents and developers to the documentation for this repository.

## Repository Purpose

LinkedIn Job Scraper — continuously scrapes LinkedIn job postings using LinkedIn's internal Voyager API. Stores results in a SQLite database and exports to CSV. Not affiliated with or endorsed by LinkedIn.

## Documentation Index

| Document | Contents |
|---|---|
| [docs/overview.md](docs/overview.md) | Architecture, module map, data flow, key design decisions |
| [docs/setup.md](docs/setup.md) | Installation, account setup, browser config, tunable parameters |
| [docs/data-model.md](docs/data-model.md) | Full database schema with ER diagram, table reference, `scraped` state machine |
| [docs/scraping-pipeline.md](docs/scraping-pipeline.md) | End-to-end pipeline flowcharts, JSON path parsing, DB write strategies |
| [docs/keyword-targeting.md](docs/keyword-targeting.md) | How to filter by keyword, location, and job type |
| [docs/running.md](docs/running.md) | Running the scraper, monitoring progress, exporting CSV, error handling |

## Key Files

| File | Role |
|---|---|
| `search_retriever.py` | Entry point: polls LinkedIn search feed, inserts job stubs |
| `details_retriever.py` | Entry point: fetches full details for unscraped jobs |
| `to_csv.py` | Exports SQLite DB to CSV files |
| `scripts/fetch.py` | `JobSearchRetriever` and `JobDetailRetriever` — all HTTP logic |
| `scripts/helpers.py` | `clean_job_postings()` — JSON response parsing |
| `scripts/database_scripts.py` | All DB insert/update logic |
| `scripts/create_db.py` | Schema creation (idempotent `CREATE TABLE IF NOT EXISTS`) |
| `json_paths/data_variables.csv` | Maps Voyager API JSON paths → DB columns (top-level `data`) |
| `json_paths/included_variables.csv` | Maps Voyager API JSON paths → DB columns (`included` array) |
| `logins.csv` | LinkedIn credentials (not committed — use `logins.csv.template`) |

## Agent Notes

- **The search URL has no keyword filter by default.** To target specific roles, edit `scripts/fetch.py` → `JobSearchRetriever.__init__` → `self.job_search_link`. See [docs/keyword-targeting.md](docs/keyword-targeting.md).
- **Authentication uses Selenium + browser cookies.** The first run of each script requires manual ENTER confirmation per account to handle login challenges.
- **Two processes must run in parallel** — `search_retriever.py` and `details_retriever.py` share the same `linkedin_jobs.db`.
- **Field extraction is config-driven**, not hardcoded. Adding or modifying scraped fields means editing the CSV files in `json_paths/`, not Python code.
- **`scraped` column** in the `jobs` table is the pipeline state: `0` = pending, `unix timestamp` = done, `-1` = error.
