"""Fleet-level checks. A single impossible fix proves little: satellite AIS drops bits, receivers mis-decode.
Two questions separate a ship that lies from a coast that lies:
  1. shared_false_cells: do many unrelated ships report the SAME impossible coordinate? A shore-based GNSS spoofer
     pushes every receiver in range to the same fake fix; a single ship's own manipulation does not.
  2. compare_groups: in the same water, is the anomaly rate of a watched group (e.g. sanctioned vessels) higher than
     that of everyone else? If not, the anomaly belongs to the place, not the ship."""
import collections
def shared_false_cells(tracks, is_false, cell_deg=0.01, min_vessels=3):
    """tracks: {mmsi: [point, ...]}; is_false(lon, lat) -> bool (e.g. inland). Returns cells sorted by distinct vessels."""
    cells = collections.defaultdict(set); fixes = collections.Counter()
    for m, tr in tracks.items():
        for p in tr:
            if is_false(p["lon"], p["lat"]):
                c = (round(round(p["lon"]/cell_deg)*cell_deg, 6), round(round(p["lat"]/cell_deg)*cell_deg, 6))
                cells[c].add(m); fixes[c] += 1
    out = [{"lon": c[0], "lat": c[1], "vessels": len(v), "fixes": fixes[c]} for c, v in cells.items() if len(v) >= min_vessels]
    return sorted(out, key=lambda x: (-x["vessels"], -x["fixes"]))
def compare_groups(flags, groups):
    """flags: {mmsi: bool (anomaly seen)}; groups: {mmsi: group label}. Returns per-group vessels, flagged, share,
    and the rate ratio of each group to the rest."""
    agg = collections.defaultdict(lambda: [0, 0])
    for m, f in flags.items():
        g = groups.get(m, "other"); agg[g][0] += 1; agg[g][1] += bool(f)
    tot_n = sum(a[0] for a in agg.values()); tot_f = sum(a[1] for a in agg.values())
    out = {}
    for g, (n, f) in agg.items():
        rest_n, rest_f = tot_n - n, tot_f - f
        share = f/n if n else 0.0; rest = rest_f/rest_n if rest_n else 0.0
        out[g] = {"vessels": n, "flagged": f, "share": round(share, 4), "ratio_to_rest": round(share/rest, 2) if rest else None}
    return out
