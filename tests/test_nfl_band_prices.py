from nfl.band_prices import band_screen, first_trade
from nfl.possessions import timestamp


def test_first_trade_uses_chronological_choice_and_inclusive_endpoints():
    assert first_trade([(19, .3), (20, .7), (40, .2)], 20, 40) == (20, .7)
    assert first_trade([(40, .2)], 20, 40) == (40, .2)
    assert first_trade([(41, .2)], 20, 40) is None


def test_actual_entry_clock_and_exit_after_offense_switch():
    start = timestamp('2026-10-11T17:00:00Z')
    plays = [dict(time_of_day='2026-10-11T17:00:00Z', qtr=4, game_seconds_remaining=180)]
    window = dict(defense_start_proxy=start, entry_time=start+30, exit_time=start+100)
    result = band_screen(window, [(start+20, .5)], [(start+99, .9), (start+110, .6)], .05, plays, 150)
    assert result['status'] == 'screened'
    assert result['exit_price'] == .6
    assert band_screen(window, [(start+40, .5)], [], .05, plays, 150)['status'] == 'late-game cutoff or unknown clock'


def test_absent_exit_does_not_fabricate_price_or_drop_missing_status():
    start = timestamp('2026-10-11T17:00:00Z')
    plays = [dict(time_of_day='2026-10-11T17:00:00Z', qtr=1, game_seconds_remaining=3600)]
    window = dict(defense_start_proxy=start, entry_time=start+30, exit_time=start+100)
    assert band_screen(window, [(start+20,.5)], [(start+121,.7)], .05, plays,150)['status'] == 'missing exit trade in 0-20s'
