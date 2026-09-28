"""Track checks. A track is a list of dicts with keys mmsi, t (datetime), lon, lat, sog (knots)."""
from .geo import haversine_km
KN = 1.852  # km/h per knot
def implied_speed_kn(a, b):
    dt_h = (b["t"] - a["t"]).total_seconds()/3600
    if dt_h <= 0: return None
    return haversine_km(a["lon"], a["lat"], b["lon"], b["lat"])/dt_h/KN
def teleports(track, vmax_kn=25.0, min_km=5.0, min_s=30):
    """Consecutive fixes whose implied speed exceeds vmax_kn (default 25 kn: above the service speed of
    large tankers and bulkers) and that are at least min_km apart. Returns list of flagged pairs."""
    out = []
    for a, b in zip(track, track[1:]):
        dt_s = (b["t"]-a["t"]).total_seconds()
        if dt_s < min_s: continue
        d = haversine_km(a["lon"], a["lat"], b["lon"], b["lat"])
        v = d/(dt_s/3600)/KN
        if d >= min_km and v > vmax_kn:
            out.append({"mmsi": a["mmsi"], "t0": a["t"].isoformat(), "t1": b["t"].isoformat(), "km": round(d, 1),
                        "implied_kn": round(v, 1), "from": [a["lon"], a["lat"]], "to": [b["lon"], b["lat"]]})
    return out
def on_land(track, grid, min_elev_m=25.0):
    """Fixes whose terrain elevation (grid) is above min_elev_m: clearly inland, not a berth. Coarse grids
    smooth coastlines, so the threshold is deliberately high."""
    return [{"mmsi": p["mmsi"], "t": p["t"].isoformat(), "lon": p["lon"], "lat": p["lat"], "elev_m": round(grid.at(p["lon"], p["lat"]))}
            for p in track if grid.contains(p["lon"], p["lat"]) and grid.at(p["lon"], p["lat"]) > min_elev_m]
def dark_gaps(track, min_h=12.0, underway_kn=3.0):
    """Silences longer than min_h hours that start while the ship reported moving (sog >= underway_kn)."""
    out = []
    for a, b in zip(track, track[1:]):
        h = (b["t"]-a["t"]).total_seconds()/3600
        if h >= min_h and (a.get("sog") or 0) >= underway_kn:
            out.append({"mmsi": a["mmsi"], "t0": a["t"].isoformat(), "t1": b["t"].isoformat(), "hours": round(h, 1),
                        "km": round(haversine_km(a["lon"], a["lat"], b["lon"], b["lat"]), 1), "from": [a["lon"], a["lat"]], "to": [b["lon"], b["lat"]]})
    return out
def split_identity(track, window_s=120, min_km=50.0):
    """Same MMSI reported in two places too far apart to be one ship within window_s seconds: a cloned or
    spoofed identity (or a receiver/decoding error; check before concluding)."""
    out = []
    for a, b in zip(track, track[1:]):
        dt_s = (b["t"]-a["t"]).total_seconds()
        if 0 <= dt_s <= window_s:
            d = haversine_km(a["lon"], a["lat"], b["lon"], b["lat"])
            if d >= min_km: out.append({"mmsi": a["mmsi"], "t": a["t"].isoformat(), "km_apart": round(d, 1), "dt_s": dt_s})
    return out
def repeating_geometry(track, cell_deg=0.01, ngram=6, min_repeats=3, moving_kn=3.0):
    """Repeated sequences of grid cells while moving: real ships do not retrace the same open-water path
    cell by cell several times; synthetic spoofed tracks often do."""
    cells = [(round(p["lon"]/cell_deg), round(p["lat"]/cell_deg)) for p in track if (p.get("sog") or 0) >= moving_kn]
    dedup = [c for i, c in enumerate(cells) if i == 0 or c != cells[i-1]]
    seen = {}
    for i in range(len(dedup)-ngram+1):
        g = tuple(dedup[i:i+ngram]); seen[g] = seen.get(g, 0) + 1
    rep = {g: n for g, n in seen.items() if n >= min_repeats}
    return {"mmsi": track[0]["mmsi"] if track else None, "repeated_ngrams": len(rep), "max_repeats": max(rep.values()) if rep else 0}
