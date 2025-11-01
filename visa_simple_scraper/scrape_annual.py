import os, re, json, time, hashlib, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

ROOT = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-statistics.html"
ALLOWED_EXTS = (".pdf", ".xlsx", ".xls")
DATA_DIR = "data/visa-statistics/annual"
MANIFEST = "data/manifest.json"
DELAY = 1

def log(msg):
    print(f"[annual] {msg}", flush=True)

def load_manifest():
    if os.path.exists(MANIFEST):
        return json.load(open(MANIFEST))
    return {"records": [], "_url_meta": {}}

def save_manifest(m):
    with open(MANIFEST, "w") as f:
        json.dump(m, f, indent=2)

def get_hash(file_path):
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()

def get_soup(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    time.sleep(DELAY)
    return BeautifulSoup(r.text, "lxml")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    manifest = load_manifest()
    log("Starting annual visa scraper...")
    soup = get_soup(ROOT)
    annual_link = None
    for a in soup.select("a[href]"):
        if "annual" in (a.text or "").lower():
            annual_link = urljoin(ROOT, a["href"])
            break
    if not annual_link:
        log("Annual reports page not found.")
        return
    psoup = get_soup(annual_link)
    for a in psoup.select("a[href]"):
        text = (a.text or "").strip()
        fy = re.search(r"(\d{4})", text)
        if not fy:
            continue
        fy = f"FY{fy.group(1)}"
        fy_url = urljoin(annual_link, a["href"])
        fy_soup = get_soup(fy_url)
        for link in fy_soup.select("a[href]"):
            href = link.get("href")
            if not href or not href.lower().endswith(ALLOWED_EXTS):
                continue
            absu = urljoin(fy_url, href)
            dest = os.path.join(DATA_DIR, fy, os.path.basename(urlparse(absu).path))
            os.makedirs(os.path.dirname(dest), exist_ok=True)

            if absu in manifest["_url_meta"]:
                log(f"Skipping existing: {absu}")
                continue

            try:
                r = requests.get(absu, timeout=60)
                r.raise_for_status()
                with open(dest, "wb") as f:
                    f.write(r.content)

                sha = get_hash(dest)
                meta_key = f"{r.headers.get('ETag')}|{r.headers.get('Last-Modified')}"
                manifest["_url_meta"][absu] = meta_key
                manifest["records"].append({
                    "url": absu,
                    "sha256": sha,
                    "bytes": len(r.content),
                    "fy": fy,
                    "variant": "annual",
                    "downloaded_at": datetime.utcnow().isoformat(),
                    "saved_to": dest
                })
                save_manifest(manifest)
                log(f"Saved {dest}")
            except Exception as e:
                log(f"ERROR downloading {absu}: {e}")
            time.sleep(DELAY)
    log("Annual scraping complete.")

if __name__ == "__main__":
    main()
