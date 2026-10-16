from nfl.possessions import windows
from nfl.price_screen import asof, observations, evaluate


def play(offense, defense, at, end=None):
    return dict(game_id='game',posteam=offense,defteam=defense,time_of_day=at,
                drive_real_start_time=at,end_clock_time=end)


def test_entry_delay_short_possessions_and_terminal_position():
    plays = [play('A','B','2026-10-11T17:00:00Z','2026-10-11T17:00:30Z'),
             play('B','A','2026-10-11T17:01:00Z','2026-10-11T17:04:00Z')]
    result = windows(plays,60)
    assert len(result)==1
    assert result[0]['team']=='A'
    assert result[0]['entry_time']-result[0]['defense_start']==60
    assert result[0]['settlement']


def test_missing_play_end_is_explicit_proxy():
    plays = [play('A','B','2026-10-11T17:00:00Z'),
             play('B','A','2026-10-11T17:05:00Z','2026-10-11T17:08:00Z')]
    first = windows(plays)[0]
    assert first['approximate_exit']
    assert first['exit_time']==windows(plays)[1]['defense_start']


def test_price_buckets_do_not_use_future_prices():
    points = observations([dict(timestamp=100,price=.4,resolution_seconds=60),
                           dict(timestamp=160,price=.8,resolution_seconds=60)])
    assert asof(points,159) is None
    assert asof(points,200)==.4
    assert asof(points,300) is None


def test_losses_fees_and_terminal_settlement_are_counted():
    window=dict(entry_time=100,exit_time=200,settlement=False)
    result=evaluate(window,[(100,.6),(200,.4)],None,.05)
    assert round(result['change_cents'])==-20
    assert round(result['fee_adjusted_change_cents'],1)==-22.4
    window['settlement']=True
    result=evaluate(window,[(100,.6)],0,.05)
    assert round(result['fee_adjusted_change_cents'],1)==-61.2
