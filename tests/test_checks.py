import unittest, datetime as dt
from aisspoof.checks import teleports, dark_gaps, split_identity, repeating_geometry, implied_speed_kn, on_land
from aisspoof.geo import haversine_km, Grid, point_in_polygon
T0 = dt.datetime(2026, 1, 1)
def p(m, s, lon, lat, sog=10.0): return {"mmsi": m, "t": T0 + dt.timedelta(seconds=s), "lon": lon, "lat": lat, "sog": sog}
class T(unittest.TestCase):
    def test_haversine_degree_lat(self):
        self.assertAlmostEqual(haversine_km(30, 44, 30, 45), 111.2, delta=0.3)
    def test_normal_ship_not_teleport(self):
        tr = [p(1, 0, 30.0, 44.0), p(1, 3600, 30.0, 44.0 + 12*1.852/111.2)]  # 12 kn for 1 h
        self.assertEqual(teleports(tr), [])
        self.assertAlmostEqual(implied_speed_kn(*tr), 12.0, delta=0.2)
    def test_teleport(self):
        tr = [p(1, 0, 30.0, 44.0), p(1, 600, 33.0, 44.0)]  # ~240 km in 10 min
        f = teleports(tr); self.assertEqual(len(f), 1); self.assertGreater(f[0]["implied_kn"], 500)
    def test_dark_gap_underway_only(self):
        self.assertEqual(len(dark_gaps([p(1, 0, 30, 44, 10), p(1, 20*3600, 31, 44)])), 1)
        self.assertEqual(dark_gaps([p(1, 0, 30, 44, 0.1), p(1, 20*3600, 30, 44)]), [])
    def test_split_identity(self):
        self.assertEqual(len(split_identity([p(1, 0, 30, 44), p(1, 60, 31.5, 44)])), 1)
    def test_repeating_geometry(self):
        loop = [(30 + 0.02*i, 44.0) for i in range(8)]
        tr = []; s = 0
        for _ in range(4):
            for lon, lat in loop: tr.append(p(1, s, lon, lat)); s += 300
            tr.append(p(1, s, 31.0, 44.5)); s += 300
        self.assertGreaterEqual(repeating_geometry(tr)["max_repeats"], 3)
    def test_on_land(self):
        g = Grid([43.0, 44.0], [28.0, 29.0], [[-100, 50], [-100, 50]])
        self.assertEqual(len(on_land([p(1, 0, 28.95, 43.5)], g)), 1)
        self.assertEqual(on_land([p(1, 0, 28.05, 43.5)], g), [])
    def test_pip(self):
        sq = [[0, 0], [1, 0], [1, 1], [0, 1]]
        self.assertTrue(point_in_polygon(0.5, 0.5, sq)); self.assertFalse(point_in_polygon(1.5, 0.5, sq))
if __name__ == "__main__": unittest.main()

from aisspoof.fleet import shared_false_cells, compare_groups
class TestFleet(unittest.TestCase):
    def test_shared_cell_needs_many_ships(self):
        t0 = dt.datetime(2026, 1, 1)
        fake = (38.11, 44.58)
        tracks = {m: [{"mmsi": m, "t": t0, "lon": fake[0], "lat": fake[1]}] for m in range(5)}
        tracks[99] = [{"mmsi": 99, "t": t0, "lon": 30.0, "lat": 44.0}]
        is_land = lambda lon, lat: lon > 38.0
        cells = shared_false_cells(tracks, is_land)
        self.assertEqual(len(cells), 1); self.assertEqual(cells[0]["vessels"], 5)
        self.assertEqual(shared_false_cells(tracks, is_land, min_vessels=6), [])
    def test_compare_groups_equal_rates(self):
        flags = {1: True, 2: False, 3: True, 4: False}
        r = compare_groups(flags, {1: "sanctioned", 2: "sanctioned"})
        self.assertEqual(r["sanctioned"]["share"], 0.5); self.assertEqual(r["sanctioned"]["ratio_to_rest"], 1.0)
