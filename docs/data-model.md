# Database Schema

The scraper stores all data in a SQLite file: `linkedin_jobs.db`.

## Entity Relationship Diagram

```mermaid
erDiagram
    jobs {
        INTEGER job_id PK
        INTEGER company_id FK
        TEXT title
        TEXT description
        TEXT location
        TEXT formatted_work_type
        TEXT work_type
        TEXT formatted_experience_level
        TEXT skills_desc
        TEXT job_posting_url
        TEXT application_url
        TEXT application_type
        TEXT posting_domain
        INTEGER applies
        INTEGER views
        INTEGER remote_allowed
        INTEGER sponsored
        TEXT original_listed_time
        TEXT listed_time
        TEXT expiry
        TEXT closed_time
        TEXT job_region
        INTEGER scraped
        TEXT inferred_benefits
        INTEGER years_experience
        TEXT degree
        TEXT currency
        TEXT compensation_type
    }

    companies {
        INTEGER company_id PK
        TEXT name
        TEXT description
        INTEGER company_size
        TEXT country
        TEXT state
        TEXT city
        TEXT zip_code
        TEXT address
        TEXT url
    }

    employee_counts {
        INTEGER company_id FK
        INTEGER employee_count
        INTEGER follower_count
        INTEGER time_recorded
    }

    company_industries {
        INTEGER company_id FK
        INTEGER industry FK
    }

    company_specialities {
        INTEGER company_id FK
        TEXT speciality
    }

    salaries {
        INTEGER salary_id PK
        INTEGER job_id FK
        FLOAT max_salary
        FLOAT med_salary
        FLOAT min_salary
        TEXT pay_period
        TEXT currency
        TEXT compensation_type
    }

    benefits {
        INTEGER job_id FK
        TEXT type
        INTEGER inferred
    }

    skills {
        TEXT skill_abr PK
        TEXT skill_name
    }

    job_skills {
        INTEGER job_id FK
        TEXT skill_abr FK
    }

    industries {
        INTEGER industry_id PK
        TEXT industry_name
    }

    job_industries {
        INTEGER job_id FK
        INTEGER industry_id FK
    }

    jobs ||--o{ salaries : "has"
    jobs ||--o{ benefits : "has"
    jobs ||--o{ job_skills : "tagged with"
    jobs ||--o{ job_industries : "categorized in"
    jobs }o--|| companies : "posted by"
    companies ||--o{ employee_counts : "tracked over time"
    companies ||--o{ company_industries : "operates in"
    companies ||--o{ company_specialities : "specializes in"
    skills ||--o{ job_skills : "referenced by"
    industries ||--o{ job_industries : "referenced by"
```

## Table Reference

### `jobs`
The central table. Rows are inserted by `search_retriever.py` with `scraped=0` and updated to `scraped=<unix_timestamp>` by `details_retriever.py`.

| Column | Type | Notes |
|---|---|---|
| `job_id` | INTEGER PK | LinkedIn's internal job ID |
| `company_id` | INTEGER FK | References `companies` |
| `title` | TEXT | Job title (populated by search phase) |
| `description` | TEXT | Full job description (details phase) |
| `location` | TEXT | Formatted location string |
| `formatted_work_type` | TEXT | Full-time, Part-time, Contract |
| `work_type` | TEXT | Raw LinkedIn employment status code |
| `formatted_experience_level` | TEXT | Entry, Associate, Mid-Senior, Director, Executive |
| `skills_desc` | TEXT | Free-text skills description from posting |
| `applies` | INTEGER | Application count |
| `views` | INTEGER | View count |
| `remote_allowed` | INTEGER | 1 if remote permitted |
| `sponsored` | INTEGER | 1 if promoted listing |
| `scraped` | INTEGER | 0 = not yet scraped; unix timestamp = scraped at; -1 = error |
| `original_listed_time` | TEXT | Original listing timestamp |
| `listed_time` | TEXT | Current listing timestamp |
| `expiry` | TEXT | Expiry timestamp |
| `closed_time` | TEXT | Closed timestamp |

### `salaries`
Multiple salary records can exist per job (different compensation types).

| Column | Type | Notes |
|---|---|---|
| `salary_id` | INTEGER PK | Auto-assigned |
| `job_id` | INTEGER FK | References `jobs` |
| `max_salary` | FLOAT | |
| `med_salary` | FLOAT | |
| `min_salary` | FLOAT | |
| `pay_period` | TEXT | HOURLY, MONTHLY, YEARLY |
| `currency` | TEXT | ISO currency code |
| `compensation_type` | TEXT | BASE_SALARY, BONUS, etc. |

### `benefits`
Each row is one benefit type for a job.

| Column | Notes |
|---|---|
| `job_id` | References `jobs` |
| `type` | e.g. "401K", "Medical Insurance", "Vision Insurance" |
| `inferred` | 0 = explicitly listed by company; 1 = inferred by LinkedIn from job text |

### `companies`

| Column | Notes |
|---|---|
| `company_id` | LinkedIn's internal company ID |
| `company_size` | Integer 0–7 encoding headcount ranges (see below) |
| `url` | LinkedIn company page URL |

**`company_size` encoding:**

| Value | Range |
|---|---|
| 0 | 1–10 |
| 1 | 11–50 |
| 2 | 51–200 |
| 3 | 201–500 |
| 4 | 501–1000 |
| 5 | 1001–5000 |
| 6 | 5001–10000 |
| 7 | 10001+ |

### `employee_counts`
Tracks headcount over time; a new row is inserted each scrape cycle.

### `skills` / `job_skills`
`skills` is a lookup table keyed by abbreviation. `job_skills` is the many-to-many join (job ↔ skill).

> **Note:** Skills here come from LinkedIn's `jobFunctions` field, not the free-text `skills_desc` field in `jobs`.

### `industries` / `job_industries`
Same pattern as skills — lookup table + join table.

### `company_industries` / `company_specialities`
Company-level industry and speciality tags stored as raw LinkedIn IDs/strings.

## `scraped` Field State Machine

```mermaid
stateDiagram-v2
    [*] --> Pending : search_retriever inserts row\n(scraped = 0)
    Pending --> Scraped : details_retriever succeeds\n(scraped = unix timestamp)
    Pending --> Error : details_retriever gets non-200\n(scraped = -1)
    Error --> [*] : row is skipped in future polls
```
