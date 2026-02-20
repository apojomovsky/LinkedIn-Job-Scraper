# Scraping Pipeline

## Pipeline Overview

```mermaid
flowchart TD
    A([Start]) --> B[Load logins.csv]
    B --> C[Selenium login per account]
    C --> D[Capture session cookies → requests.Session]
    D --> E{Which script?}

    E -->|search_retriever.py| F[GET voyager jobSearch feed]
    F --> G[Parse job cards from included array]
    G --> H[Filter: only JobPostingCard types with referenceId]
    H --> I[Extract job_id, title, sponsored flag]
    I --> J{Already in DB?}
    J -->|No| K[INSERT into jobs with scraped=0]
    J -->|Yes| L[Skip]
    K --> M[Log: X/Y new results]
    L --> M
    M --> N[Adaptive sleep 0–200s]
    N --> F

    E -->|details_retriever.py| O[SELECT job_id WHERE scraped=0]
    O --> P[Random sample up to MAX_UPDATES]
    P --> Q[GET voyager jobPostings per ID]
    Q --> R{Status 200?}
    R -->|No| S[Mark scraped=-1\nincrement error_count]
    S --> T{error_count > 10?}
    T -->|Yes| U([Raise Exception])
    T -->|No| V[Continue to next ID]
    R -->|Yes| W[clean_job_postings]
    W --> X[Parse via data_variables.csv paths]
    W --> Y[Parse via included_variables.csv paths]
    X --> Z[insert_data to DB]
    Y --> Z
    Z --> AA[Sleep SLEEP_TIME seconds]
    AA --> O
```

## Search Retriever Detail

`search_retriever.py` calls a single LinkedIn Voyager endpoint that returns a paginated job search feed. Key behaviors:

- Calls `voyagerJobsDashJobCards` with `count=100` and `sortBy:DD` (date descending)
- Iterates through `results['included']` looking for `$type == JobPostingCard` entries with a `referenceId`
- Extracts `jobPostingUrn` (splits on `:` to get the numeric ID) and checks for `PROMOTED` footer items
- **No keyword filter by default** — see [keyword-targeting.md](keyword-targeting.md) to add one
- Session is rotated round-robin across all `search` accounts

**Adaptive sleep logic:**
```
seconds_per_job = sleep_factor / max(new_results, 1)
sleep_factor    = min(seconds_per_job × total_non_sponsored × 0.75, 200)
```
This means sleep shrinks when many new jobs are found and grows when the feed is saturated.

## Details Retriever Detail

`details_retriever.py` fetches one job per HTTP request from `voyager/api/jobs/jobPostings/{job_id}`.

- Randomly samples up to `MAX_UPDATES` unscraped jobs per cycle to avoid predictable patterns
- 300ms delay between each individual job request
- Rotates through all `details` accounts round-robin
- Raises a fatal exception after 10 consecutive errors (likely IP/account ban)

## JSON Path Parsing

Field extraction is data-driven — no hardcoded per-field parsing. Two CSV config files define which JSON paths map to which DB columns:

### `json_paths/data_variables.csv`
Paths into the top-level `data` key of the job detail response.

| Column | Meaning |
|---|---|
| `path` | Python dict-access path string, e.g. `['data']['title']` |
| `name` | Target DB column name |
| `strip` | Post-processing: `0`=raw, `1`=split on `:` take last, `2`=split on `.` take last |
| `table` | Target DB table |

### `json_paths/included_variables.csv`
Paths into objects in the `included` array (used for company data, follower counts, etc.).

| Column | Meaning |
|---|---|
| `path` | Dict path within each `included` item |
| `name` | Target DB column name |
| `type` | Filters `included` items by their `$type` suffix (e.g. `Company`, `FollowingInfo`) |
| `table` | Target DB table |

## `clean_job_postings()` Logic

```mermaid
flowchart LR
    A[raw API response per job_id] --> B{Status -1?}
    B -->|Yes| C[Return error dict]
    B -->|No| D[Init empty dict:\njobs / companies / salaries /\nbenefits / industries / skills /\nemployee_counts / company_industries /\ncompany_specialities]
    D --> E[Iterate data_variables.csv rows]
    E --> F[get_value_by_path on data dict]
    F --> G[strip_val based on strip column]
    G --> H[Store in posting table dict]
    D --> I[Iterate included_variables.csv rows]
    I --> J[Find matching type in included array]
    J --> K{company_size?}
    K -->|Yes| L[Map staffCountRange to 0-7 integer]
    K -->|No| M[get_value_by_path + strip_val]
    L --> H
    M --> H
    H --> N[Return cleaned posting dict]
```

## Database Write Logic

`insert_data()` in `scripts/database_scripts.py` handles each table differently:

| Table | Write Strategy |
|---|---|
| `jobs` | `UPDATE` (row already exists from search phase) |
| `benefits` | `INSERT OR REPLACE` for listed; `INSERT OR IGNORE` for inferred |
| `industries` | `INSERT OR REPLACE` with `COALESCE` to preserve existing name |
| `skills` | Same as industries |
| `salaries` | `INSERT` (allows multiple per job) |
| `companies` | `INSERT OR REPLACE` |
| `employee_counts` | `INSERT OR IGNORE` (preserves historical snapshots) |
| `company_industries` | `INSERT OR IGNORE` |
| `company_specialities` | `INSERT OR IGNORE` |
