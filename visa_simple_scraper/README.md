# Visa Statistics Scraper

Downloads visa issuance data from the Department of State website. Scrapes monthly and annual reports and saves them locally with a JSON manifest.

## Setup

```bash
pip install -r requirements.txt
python scrape_monthly.py
python scrape_annual.py
python run_all.py
```

## API

```bash
uvicorn app:app --reload --port 8080
```

Endpoints:
- `GET /healthz`
- `POST /run/{monthly|annual|all}`
- `GET /list`

## Docker

```bash
docker build -t visa-simple .
docker run -p 8080:8080 -v $(pwd)/data:/app/data visa-simple
```

```json
{
  "records": [
    {
      "url": "https://travel.state.gov/.../FY2024-09-IV.xlsx",
      "sha256": "a1b2c3...",
      "bytes": 24576,
      "fy": "FY2024",
      "variant": "iv",
      "downloaded_at": "2025-10-31T21:12:00",
      "saved_to": "data/visa-statistics/monthly/iv/FY2024/FY2024-09-IV.xlsx"
    }
  ],
  "_url_meta": {
    "https://travel.state.gov/...": "etag123|Wed, 08 Oct 2025 18:22:01 GMT"
  }
}
```

---



