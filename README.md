# ais-spoof-check

**Is this ship lying about where it is, or is the coast lying to every ship?**

A small, dependency-free toolkit that tests AIS vessel tracks against physics, and then against the other ships in the same water. Built for, and used in, the DarkAnalytica investigation *Positions that lie* (Black Sea, September 2025 to March 2026).

## Why it matters

Impossible AIS positions are easy to find in the Black Sea, and easy to read as a sanctioned tanker hiding something. In six months of open AIS for the whole sea (6.1 million positions, 5,904 vessels), 1,674 vessels reported at least one position far inland. But the false points are shared: one spot on the Taman peninsula was reported by 644 different ships. In the Kerch-Novorossiysk area, listed and unlisted vessels show inland positions at the same rate (85 %). A single-ship detector would have flagged the coast.

So this toolkit has two layers:

1. **Track checks** (`aisspoof.checks`): per-vessel physics.
2. **Fleet checks** (`aisspoof.fleet`): is the anomaly shared by many unrelated ships, and is a watched group affected more than everyone else in the same area?

## Checks

| Function | What it flags |
|---|---|
| `teleports(track, vmax_kn=25, min_km=5)` | consecutive fixes implying an impossible speed |
| `on_land(track, grid, min_elev_m=25)` | fixes clearly inland on a terrain or land-mask grid |
| `dark_gaps(track, min_h=12)` | silences that start while the ship was under way |
| `split_identity(track, window_s=120, min_km=50)` | one MMSI in two distant places within seconds |
| `repeating_geometry(track)` | the same cell sequence retraced several times (synthetic tracks) |
| `fleet.shared_false_cells(tracks, is_false)` | impossible points reported by many distinct vessels |
| `fleet.compare_groups(flags, groups)` | anomaly share per group and ratio to everyone else |

## Quick start (verified)

```bash
python -m unittest discover -s tests          # 10 tests, standard library only
python -m aisspoof positions.json.gz --grid grid.json > flags.json
```

Input: a JSON list of Kystdatahuset-style rows `[mmsi, iso_time, lon, lat, cog, sog, ...]` or dicts with `mmsi, t, lon, lat, sog`. The grid is `{"lats": [...], "lons": [...], "z": [[...]]}` (elevation in metres, positive on land).

```python
from aisspoof.fleet import compare_groups
compare_groups({1: True, 2: False, 3: True, 4: False}, {1: "listed", 2: "listed"})
# {'listed': {'vessels': 2, 'flagged': 1, 'share': 0.5, 'ratio_to_rest': 1.0}, 'other': {...}}
```

## Limits

- A single impossible fix proves little: satellite AIS drops and corrupts messages. Use the fleet checks before concluding anything.
- A smooth, physically plausible false track passes every check here. Catching it needs independent evidence such as radar satellite imagery.
- Coarse land masks blur coastlines; erode them (the investigation used about 3 km) and exclude navigable rivers and canals.
- Shared inland points indicate the environment (for example shore-based GNSS spoofing); the toolkit does not identify the transmitter.

## Data used in the investigation

Norwegian Coastal Administration open AIS (Kystdatahuset API, NLOD licence); OpenSanctions consolidation of EU, UK, US, Canadian, Swiss and Ukraine GUR vessel lists; Black Sea MoU detention list; Natural Earth 10 m land; GEBCO 2020; Marine Regions EEZ. Raw data is not redistributed here.

## References

- C4ADS, *Above Us Only Stars: Exposing GPS Spoofing in Russia and Syria* (2019).
- SkyTruth, "Tankers Falsify AIS Tracking Positions to Hide Entry into Russian Black Sea Ports" (2023).
- EASA Safety Information Bulletin 2022-02R4 (2026).

MIT License · Leonard Dumitru
