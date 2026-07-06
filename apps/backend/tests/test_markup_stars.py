"""Markup arithmetic: 0 stays 0, positive prices scale and never drop below 1."""
from scripts.markup_stars import bumped


def test_bumped():
    assert bumped(500, 1.54) == 770   # "$10" at 0.02 -> nets ~$10 at 0.013
    assert bumped(0, 1.54) == 0       # free / unpriced stays put
    assert bumped(1, 1.54) == 2       # rounds, never below 1
