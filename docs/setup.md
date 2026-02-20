# Setup & Configuration

## Prerequisites

- Python 3.8+
- **Microsoft Edge** browser (default) **or** Google Chrome
- Matching WebDriver:
  - Edge: [Microsoft Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
  - Chrome: [ChromeDriver](https://chromedriver.chromium.org/)
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
| `pandas>=2.1.1` | CSV loading, data handling |

## Browser Configuration

By default, the scraper uses **Microsoft Edge**. To switch to Chrome, edit `scripts/fetch.py` line 11:

```python
BROWSER = 'chrome'   # was 'edge'
```

## Account Setup (`logins.csv`)

Copy the template and fill in real credentials:

```bash
cp logins.csv.template logins.csv
```

Format:
```csv
emails,passwords,method
search_account@gmail.com,password1,search
details_account1@gmail.com,password2,details
details_account2@gmail.com,password3,details
```

### Account Roles

| Method | Usage | Recommended Count |
|---|---|---|
| `search` | Polls the job search feed | 1–3 |
| `details` | Fetches full data per job ID | As many as possible |

Details fetching is far more API-intensive (one HTTP call per job). More `details` accounts = higher throughput and lower per-account ban risk.

> **Security note:** `logins.csv` is in `.gitignore`. Never commit it.

## Login Flow

On first run of each script, Selenium opens a real browser window for each account in `logins.csv`:

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
