"""Fetch yesterday's and the prior 7 days' visitor totals from GoatCounter's public counter
and save them to stats/latest.json (plus a running stats/history.csv)."""
import json, os, csv, urllib.request, urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

CODE = "bobsbake"
tz = ZoneInfo("America/New_York")
today = datetime.now(tz).date()
y = today - timedelta(days=1)
b_start, b_end = y - timedelta(days=7), y - timedelta(days=1)

def total(start, end):
    url = f"https://{CODE}.goatcounter.com/counter/TOTAL.json?start={start}&end={end}"
    req = urllib.request.Request(url, headers={"User-Agent": "bobs-sourdough-stats"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return int(str(json.load(r)["count"]).replace(",", "").replace(" ", "").replace(" ", "") or 0)
    except urllib.error.HTTPError as e:
        if e.code == 404:  # no visits in that range
            return 0
        raise

out = {"checked_at": datetime.now(tz).isoformat(timespec="seconds"), "date": str(y)}
try:
    yv = total(y, y)
    bt = total(b_start, b_end)
    avg = round(bt / 7, 1)
    out.update(yesterday=yv, baseline_total=bt, baseline_avg=avg,
               spike=bool(yv >= 10 and yv >= 2 * avg), error=None)
except Exception as e:
    out.update(error=f"{type(e).__name__}: {e}")

os.makedirs("stats", exist_ok=True)
json.dump(out, open("stats/latest.json", "w"), indent=2)
if not out["error"]:
    new = not os.path.exists("stats/history.csv")
    with open("stats/history.csv", "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["date", "visitors", "prior_7_day_avg", "spike"])
        w.writerow([out["date"], out["yesterday"], out["baseline_avg"], out["spike"]])
print(json.dumps(out))
