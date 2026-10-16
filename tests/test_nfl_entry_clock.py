from nfl.entry_clock import entry_allowed
from nfl.possessions import timestamp


def test_cutoff_uses_entry_time_and_ignores_future_clock():
    start = timestamp('2026-10-11T17:00:00Z')
    plays = [dict(time_of_day='2026-10-11T17:00:00Z', qtr=4, game_seconds_remaining=330),
             dict(time_of_day='2026-10-11T17:01:00Z', qtr=4, game_seconds_remaining=100)]
    assert entry_allowed(plays, start + 29, 300)
    assert not entry_allowed(plays, start + 30, 300)


def test_overtime_and_missing_clock_do_not_open_positions():
    at = '2026-10-11T17:00:00Z'
    assert not entry_allowed([dict(time_of_day=at, qtr=5, game_seconds_remaining=600)], timestamp(at), 300)
    assert not entry_allowed([dict(time_of_day=at, qtr=4, game_seconds_remaining=None)], timestamp(at), 300)
