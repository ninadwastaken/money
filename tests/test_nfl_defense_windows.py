from nfl.defense_windows import defense_windows
from nfl.trade_prices import screen


def play(offense, defense, at):
    return dict(game_id='game', posteam=offense, defteam=defense, time_of_day=at,
                drive_real_start_time=at, end_clock_time=None)


def test_exit_waits_for_return_to_offense_and_final_hold_is_retained():
    plays = [play('A', 'B', '2026-10-11T17:00:00Z'),
             play('A', 'B', '2026-10-11T17:02:00Z'),
             play('B', 'A', '2026-10-11T17:05:00Z'),
             play('A', 'B', '2026-10-11T17:10:00Z')]
    result = defense_windows(plays)
    assert len(result) == 3
    assert result[0]['team'] == 'B'
    assert result[0]['entry_time'] - result[0]['defense_start_proxy'] == 30
    assert result[0]['exit_time'] == result[1]['defense_start_proxy']
    assert result[-1]['settlement']


def test_short_possessions_are_counted_without_entering_after_the_switch():
    result = screen(dict(entry_time=130, exit_time=120), [], [], .05)
    assert result['status'] == 'possession ended before entry'


def test_no_return_to_offense_uses_official_payout_and_keeps_losses():
    result = screen(dict(entry_time=100, exit_time=300), [(100, .5)], [], .05, payout=0)
    assert result['hypothetical_profit'] == -10
    assert result['exit_price'] == 0
