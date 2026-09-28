"""CLI: python -m aisspoof input.json [--grid grid.json] > flags.json
input: JSON list of [mmsi, iso_time, lon, lat, cog, sog, ...] rows (Kystdatahuset position format) or dicts."""
import sys, json, gzip, datetime as dt, argparse, collections
from .checks import teleports, on_land, dark_gaps, split_identity, repeating_geometry
from .geo import Grid
def load(path):
    op = gzip.open if path.endswith(".gz") else open
    rows = json.load(op(path, "rt"))
    out = []
    for r in rows:
        if isinstance(r, dict): out.append({"mmsi": r["mmsi"], "t": dt.datetime.fromisoformat(r["t"]), "lon": r["lon"], "lat": r["lat"], "sog": r.get("sog")})
        else: out.append({"mmsi": r[0], "t": dt.datetime.fromisoformat(r[1]), "lon": r[2], "lat": r[3], "sog": r[5]})
    return out
def analyse(points, grid=None):
    by = collections.defaultdict(list)
    for p in points: by[p["mmsi"]].append(p)
    res = {"vessels": len(by), "positions": len(points), "teleports": [], "on_land": [], "dark_gaps": [], "split_identity": [], "repeating": []}
    for m, tr in by.items():
        tr.sort(key=lambda p: p["t"])
        res["teleports"] += teleports(tr); res["dark_gaps"] += dark_gaps(tr); res["split_identity"] += split_identity(tr)
        if grid: res["on_land"] += on_land(tr, grid)
        rg = repeating_geometry(tr)
        if rg["repeated_ngrams"]: res["repeating"].append(rg)
    return res
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--grid")
    a = ap.parse_args()
    grid = None
    if a.grid:
        g = json.load(open(a.grid)); grid = Grid(g["lats"], g["lons"], g["z"])
    json.dump(analyse(load(a.input), grid), sys.stdout, indent=1)
if __name__ == "__main__": main()
