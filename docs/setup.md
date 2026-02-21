# Setup & Configuration

## Prerequisites

- Python 3.8+
- **Google Chrome** browser
- One or more LinkedIn accounts

## Installation

```bash
pip install -r requirements.txt
```

Dependencies:
| Package | Purpose |
|---|---|
| `selenium>=4.14.0` | Browser automation for initial login |
| `requests>=2.31.0` | All API calls after login |
| `pandas>=2.1.1` | Data handling |
| `python-dotenv>=1.0.0` | Load credentials from `.env` |

## Browser Configuration

Chrome is used by default. ChromeDriver is managed automatically by Selenium — no manual installation needed.

## Account Setup (`.env`)

Copy the example and fill in your credentials:

```bash
cp .env.example .env
```

```ini
SEARCH_EMAILS=your_email@gmail.com
SEARCH_PASSWORDS=your_password

DETAILS_EMAILS=your_email@gmail.com
DETAILS_PASSWORDS=your_password
```

### Multiple accounts

For higher throughput, use comma-separated values:

```ini
DETAILS_EMAILS=account1@gmail.com,account2@gmail.com
DETAILS_PASSWORDS=password1,password2
```

| Variable | Used by | Recommended count |
|---|---|---|
| `SEARCH_EMAILS` / `SEARCH_PASSWORDS` | `search_retriever.py` | 1–3 |
| `DETAILS_EMAILS` / `DETAILS_PASSWORDS` | `details_retriever.py` | As many as possible |

Details fetching is far more API-intensive (one HTTP call per job). More accounts = higher throughput and lower per-account ban risk.

> **Security note:** `.env` is in `.gitignore`. Never commit it. Commit `.env.example` instead.

## Login Flow

On first run of each script, Selenium opens a real browser window for each account in `.env`:

1. Browser navigates to LinkedIn sign-in
2. Credentials are typed automatically
3. **You must manually press ENTER in the terminal** after confirming the login succeeded (handles 2FA, CAPTCHA, etc.)
4. The script captures session cookies and closes the browser
5. All subsequent requests use those cookies — no browser needed

## Tunable Parameters

### `details_retriever.py`

```python
SLEEP_TIME = 60      # Seconds to sleep between each iteration
MAX_UPDATES = 25     # Max job details to fetch per iteration
```

Increase `MAX_UPDATES` when you have more accounts or proxies.

### `search_retriever.py`

Sleep time is **adaptive** — it calculates seconds-per-new-job and scales accordingly, capping at 200 seconds. No manual tuning needed, but the `sleep_factor = 3` initial value and `*.75` dampening factor on line 36–37 can be adjusted.

## Keyword / Location Targeting

See [keyword-targeting.md](keyword-targeting.md) for full details on filtering search results by keyword and location.

## Proxies

Proxy support is stubbed but commented out in `scripts/fetch.py`:

```python
# self.proxies = [{'http': f'http://{proxy}', 'https': f'http://{proxy}'} for proxy in []]
```

To enable, populate the list with proxy strings and uncomment the `proxies=` argument in `get_job_details()`.
