# LinkedIn Job Scraper

<img src="media/logo.jpg" width="530" height="267">

**Scrapes and stores a continuous stream of LinkedIn job postings and their full attributes — title, description, salary, skills, benefits, company info, and more — into a local SQLite database.**

> 📦 A pre-built dataset is also available on [Kaggle](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings).

---

## How it works

Two scripts run in parallel and share a SQLite database (`linkedin_jobs.db`):

| Script | Role |
|---|---|
| `search_retriever.py` | Polls LinkedIn's job feed. Collects job IDs matching your searches. Fast — one API call returns ~100 results. |
| `details_retriever.py` | Reads those job IDs and fetches full details for each one (salary, skills, company, benefits, etc.). Heavier — one API call per job. |

---

## Setup

### 1. Install dependencies

```bash
uv venv .venv
uv pip install -r requirements.txt
source .venv/bin/activate
```

Or with plain pip:

```bash
pip install -r requirements.txt
```

Requires **Python 3.8+** and **Google Chrome** (ChromeDriver is managed automatically by Selenium).

### 2. Configure your LinkedIn accounts — `logins.csv`

Copy the template and fill in your credentials:

```bash
cp logins.csv.template logins.csv
```

```csv
emails,passwords,method
your_email@gmail.com,your_password,search
your_email@gmail.com,your_password,details
```

The `method` column controls which script uses each account:

| Value | Used by |
|---|---|
| `search` | `search_retriever.py` |
| `details` | `details_retriever.py` |

The same account can be used for both. For higher throughput and lower ban risk on the details side, add more `details` accounts — one row per account.

> `logins.csv` is gitignored. Never commit it.

### 3. Configure your searches — `search_config.csv`

Edit `search_config.csv` to define what jobs you want to scrape. Each row is one search. All searches run every cycle and results are merged automatically.

```csv
keywords,geo_urn,job_type,experience
data engineer,103644278,,
machine learning engineer,103644278,,
python developer,,F,4
```

| Column | Required | Description |
|---|---|---|
| `keywords` | No | Job search terms. Plain text, spaces allowed. |
| `geo_urn` | No | LinkedIn location ID. See table below. |
| `job_type` | No | `F`=Full-time, `P`=Part-time, `C`=Contract, `I`=Internship |
| `experience` | No | `2`=Entry, `3`=Associate, `4`=Mid-Senior, `5`=Director, `6`=Executive |

Leave any column blank to skip that filter. An empty row (all blank) scrapes the default LinkedIn feed with no filters.

**Common `geo_urn` values:**

| Location | geo_urn |
|---|---|
| United States | `103644278` |
| United Kingdom | `101165590` |
| Canada | `101174742` |
| Germany | `101282230` |
| Australia | `101452733` |
| Remote (worldwide) | `90000084` |

To find a geo_urn for another location: go to LinkedIn Jobs, apply a location filter, open DevTools → Network, and look for a `voyagerJobsDashJobCards` request — the `geoUrn` value will be in the query string.

---

## Running

### Option A — single command (recommended)

```bash
python run.py
```

Launches both scripts in parallel. Login happens automatically after a 15-second wait per account. Increase it if LinkedIn shows extra verification steps:

```bash
python run.py --login-wait 30
```

### Option B — two terminals

Open **two terminals** and run both scripts in parallel:

```bash
# Terminal 1 — discovers new job IDs
python search_retriever.py

# Terminal 2 — fetches full job details
python details_retriever.py
```

On first run, a Chrome window opens for each account. After the LinkedIn homepage loads, **press Enter in the terminal** to confirm login (this handles 2FA and CAPTCHA manually). The browser closes and all further requests are headless.

### Optional tuning (`details_retriever.py`)

```python
SLEEP_TIME = 60    # seconds between each batch
MAX_UPDATES = 25   # jobs to fetch per batch — increase with more accounts
```

`search_retriever.py` auto-adjusts its sleep time based on how many new results it finds (up to 200 seconds when the feed is saturated).

### Tips for reliability

- `details_retriever.py` is more likely to get rate-limited. Use multiple accounts, longer sleep times, or run it during off-peak hours (nights, weekends).
- `search_retriever.py` typically runs fine on a single account.
- If you hit 10 consecutive errors in `details_retriever.py`, it will stop — restart to re-authenticate.

---

## Database fields

### Core job fields (populated by `details_retriever.py`)

| Field | Description |
|---|---|
| `job_id` | LinkedIn's internal job ID |
| `title` | Job title |
| `description` | Full job description text |
| `location` | Formatted location string |
| `formatted_work_type` | Full-time, Part-time, Contract |
| `formatted_experience_level` | Entry, Associate, Mid-Senior, Director, Executive |
| `skills_desc` | Free-text skills description from the posting |
| `applies` | Number of applications submitted |
| `views` | Number of times the posting was viewed |
| `remote_allowed` | Boolean — whether remote work is permitted |
| `workplace_type` | `1`=On-site, `2`=Remote, `3`=Hybrid (structured, from `workplaceTypes`) |
| `job_state` | `LISTED` or `CLOSED` |
| `applicant_tracking_system` | ATS used by the company (e.g. Lever, Greenhouse, Workday) |
| `job_posting_url` | URL to the LinkedIn job posting |
| `application_url` | URL where applications are submitted |
| `application_type` | `SimpleOnsiteApply`, `ComplexOnsiteApply`, or offsite |
| `posting_domain` | Domain of the external application site |
| `sponsored` | Whether the listing is promoted |
| `original_listed_time` | Unix ms timestamp of original listing |
| `listed_time` | Unix ms timestamp of current listing |
| `expiry` | Unix ms timestamp of expiry |
| `closed_time` | Unix ms timestamp when closed |
| `company_id` | References the `companies` table |

### Related tables

| Table | What it holds |
|---|---|
| `companies` | Name, description, size, HQ location, LinkedIn URL |
| `employee_counts` | Headcount + follower snapshots over time |
| `salaries` | Min/med/max salary, pay period, currency (when LinkedIn provides it) |
| `benefits` | Listed and inferred benefits (401K, medical, etc.) |
| `skills` / `job_skills` | LinkedIn job function categories per job |
| `industries` / `job_industries` | Industry tags per job |
| `company_industries` / `company_specialities` | Company-level industry and speciality tags |

> Fields marked as rarely populated in practice: `years_experience`, `job_region`, `degree`, `salary` (LinkedIn surfaces salary data for <10% of postings).

---



```bash
python to_csv.py --folder ./output --database linkedin_jobs.db
```

Creates one CSV per table plus a merged `job_postings.csv` (jobs + salaries joined, only fully-scraped rows).

---

## Monitoring progress

```bash
sqlite3 linkedin_jobs.db "
SELECT
  COUNT(*) AS total,
  SUM(CASE WHEN scraped = 0 THEN 1 ELSE 0 END) AS pending,
  SUM(CASE WHEN scraped > 0 THEN 1 ELSE 0 END) AS done,
  SUM(CASE WHEN scraped = -1 THEN 1 ELSE 0 END) AS errors
FROM jobs;"
```

---

## Database structure

See [DatabaseStructure.md](DatabaseStructure.md) for the full schema, or [docs/data-model.md](docs/data-model.md) for an ER diagram.

---

## Documentation

Extended documentation with architecture diagrams, pipeline flowcharts, and more lives in [`docs/`](docs/):

| Doc | Contents |
|---|---|
| [docs/overview.md](docs/overview.md) | Architecture and data flow |
| [docs/setup.md](docs/setup.md) | Detailed setup and configuration |
| [docs/data-model.md](docs/data-model.md) | Database schema with ER diagram |
| [docs/scraping-pipeline.md](docs/scraping-pipeline.md) | How the pipeline works internally |
| [docs/keyword-targeting.md](docs/keyword-targeting.md) | Search filters reference |
| [docs/running.md](docs/running.md) | Running, monitoring, and error handling |

