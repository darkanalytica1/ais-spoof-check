"""ais-spoof-check: physics and consistency checks for AIS tracks.

Flags positions and track segments that a real ship could not have produced:
teleports (implied speed impossible for the hull), positions on land, one MMSI in two
places at once, long silences while underway, and repeating track geometry.
Standard library only."""
__version__ = "0.2.0"
