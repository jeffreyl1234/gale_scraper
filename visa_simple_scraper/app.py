from fastapi import FastAPI, HTTPException
import subprocess, os, json

app = FastAPI(title="Simple Visa Scraper")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/run/{source}")
def run_scraper(source: str):
    if source not in ["monthly", "annual", "all"]:
        raise HTTPException(400, "Invalid source")
    script = {
        "monthly": "scrape_monthly.py",
        "annual": "scrape_annual.py",
        "all": "run_all.py"
    }[source]
    try:
        subprocess.check_call(["python", script])
        return {"status": "success", "source": source}
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"Scraper failed: {e}")

@app.get("/list")
def list_files():
    path = "data/manifest.json"
    if not os.path.exists(path):
        return {"records": 0}
    return json.load(open(path))
