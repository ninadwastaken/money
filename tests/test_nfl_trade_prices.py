from nfl.trade_prices import recent_trade, screen, trade_series


def test_same_second_trades_use_volume_weights_and_filter_side():
    rows = [dict(token_id='a', side='BUY', timestamp=100, price=.4, size=3),
            dict(token_id='a', side='BUY', timestamp=100, price=.8, size=1),
            dict(token_id='a', side='SELL', timestamp=100, price=.1, size=10)]
    assert trade_series(rows, 'a', 'BUY') == [(100, .5)]


def test_future_and_stale_trades_are_excluded():
    assert recent_trade([(100, .4)], 99, 5) is None
    assert recent_trade([(100, .4)], 106, 5) is None
    assert recent_trade([(100, .4)], 105, 5) == (100, .4)


def test_stake_includes_buy_fee_and_losses_are_retained():
    result = screen(dict(entry_time=100, exit_time=150), [(100, .5)], [(150, .4)], .05)
    assert result['status'] == 'screened'
    assert abs(result['hypothetical_profit'] - (10 / .5125 * .388 - 10)) < 1e-9
    assert screen(dict(entry_time=100, exit_time=150), [], [], .05)['status'] == 'missing recent trade'
