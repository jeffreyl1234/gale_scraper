import subprocess

print("[runner] Starting all scrapers...")
subprocess.call(["python", "scrape_monthly.py"])
subprocess.call(["python", "scrape_annual.py"])
print("[runner] Done.")
