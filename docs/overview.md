# Architecture Overview

This tool scrapes LinkedIn job postings using LinkedIn's internal Voyager API (not the public API). It is split into two independent processes that run in parallel and share a SQLite database.

## High-Level Architecture

```mermaid
graph TD
    A[LinkedIn Voyager API] -->|search results| B[search_retriever.py]
    A -->|job details| C[details_retriever.py]

    B -->|INSERT job_id + title + sponsored| D[(linkedin_jobs.db)]
    C -->|SELECT scraped=0| D
    C -->|UPDATE full job details| D

    D -->|export| E[to_csv.py]
    E --> F[job_postings.csv + per-table CSVs]

    subgraph Authentication
        G[logins.csv] -->|search accounts| B
        G -->|details accounts| C
        H[Selenium browser login] -->|session cookies| B
        H -->|session cookies| C
    end
```

## Process Responsibilities

| Process | Script | Role |
|---|---|---|
| Search Retriever | `search_retriever.py` | Polls LinkedIn search feed. Extracts job IDs + title + sponsored status. Writes stub rows to `jobs` table. |
| Details Retriever | `details_retriever.py` | Reads unscraped job IDs from DB. Fetches full job data per-ID. Populates all tables. |
| CSV Exporter | `to_csv.py` | Dumps all DB tables to CSV files. Produces a merged `job_postings.csv`. |

## Module Map

```mermaid
graph LR
    SR[search_retriever.py] --> CD[scripts/create_db.py]
    SR --> DB[scripts/database_scripts.py]
    SR --> FE[scripts/fetch.py → JobSearchRetriever]

    DR[details_retriever.py] --> CD
    DR --> DB
    DR --> FE2[scripts/fetch.py → JobDetailRetriever]
    DR --> HE[scripts/helpers.py → clean_job_postings]

    FE --> HE2[scripts/helpers.py → strip_val]
    FE2 --> JP[json_paths/data_variables.csv]
    HE --> JP
    HE --> JP2[json_paths/included_variables.csv]
```

## Data Flow

```mermaid
sequenceDiagram
    participant SR as search_retriever.py
    participant DR as details_retriever.py
    participant LI as LinkedIn Voyager API
    participant DB as linkedin_jobs.db

    loop Every ~30-200s
        SR->>LI: GET jobSearch (feed)
        LI-->>SR: 25-100 job cards
        SR->>DB: INSERT OR IGNORE into jobs (job_id, title, sponsored)
    end

    loop Every 60s
        DR->>DB: SELECT job_id WHERE scraped=0
        DR->>LI: GET jobPostings/{id} × MAX_UPDATES
        LI-->>DR: Full job JSON per ID
        DR->>DR: clean_job_postings() — parse via json_paths CSVs
        DR->>DB: UPDATE jobs + INSERT into salaries, benefits,\ncompanies, skills, industries, employee_counts
    end
```

## Key Design Decisions

- **No official API** — Uses the same internal `voyager/api` endpoints the LinkedIn web app uses, authenticated via browser session cookies captured through Selenium.
- **Cookie-based auth** — Selenium logs in once per account, captures cookies into a `requests.Session`, then the browser is closed. All subsequent calls are headless HTTP.
- **Two-speed pipeline** — Search is cheap (one call = ~100 jobs). Detail fetching is expensive (one call per job). Separate accounts + rate limiting keep both from getting blocked.
- **Adaptive sleep** — `search_retriever.py` adjusts its sleep time based on how many new results it's finding, slowing down when the feed is saturated.
- **JSON path mapping** — `json_paths/data_variables.csv` and `included_variables.csv` are configuration files that map LinkedIn's API response JSON paths to DB column names — no hardcoded parsing logic per field.
