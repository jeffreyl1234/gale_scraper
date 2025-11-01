import os, re, json, time, hashlib, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

ROOT = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-statistics.html"
ALLOWED_EXTS = (".pdf", ".xlsx", ".xls")
DATA_DIR = "data/visa-statistics/monthly"
MANIFEST = "data/manifest.json"
DELAY = 1


def log(msg):
    print(f"[monthly] {msg}", flush=True)


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
    log("Starting monthly visa scraper...")

    soup = get_soup(ROOT)
    links = {}
    for a in soup.select("a[href]"):
        text = (a.text or "").strip().lower()
        if "monthly immigrant visa" in text:
            links["iv"] = urljoin(ROOT, a["href"])
        elif "monthly nonimmigrant visa" in text:
            links["niv"] = urljoin(ROOT, a["href"])

    for program, url in links.items():
        log(f"Scanning {program.upper()} page: {url}")
        psoup = get_soup(url)

        for a in psoup.select("a[href]"):
            href = a.get("href")
            if not href or not href.lower().endswith(ALLOWED_EXTS):
                continue
            absu = urljoin(url, href)
            fy = re.search(r"FY\s?(\d{4})", a.text or "") or re.search(r"(20\d{2})", a.text or "")
            fy = f"FY{fy.group(1)}" if fy else "unknown"
            dest = os.path.join(DATA_DIR, program, fy, os.path.basename(urlparse(absu).path))
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
                    "variant": program,
                    "downloaded_at": datetime.utcnow().isoformat(),
                    "saved_to": dest
                })
                save_manifest(manifest)
                log(f"Saved {dest}")
            except Exception as e:
                log(f"ERROR downloading {absu}: {e}")
            time.sleep(DELAY)
    log("Monthly scraping complete.")


if __name__ == "__main__":
    main()
