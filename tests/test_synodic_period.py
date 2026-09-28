"""Synodic period relation for inferior and superior planets."""

from src.physics import synodic_period_days


def test_mars_synodic_period_is_about_780_days():
    # Mars is a superior planet. Sidereal period is about 687 days.
    s = synodic_period_days(686.98, superior=True)
    assert abs(s - 780) < 2


def test_venus_synodic_period_is_about_584_days():
    # Venus is an inferior planet. Sidereal period is about 225 days.
    s = synodic_period_days(224.70, superior=False)
    assert abs(s - 584) < 2
