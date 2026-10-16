import math
import pytest
from btc.candles import history
from btc.score import summary
from strategies.models.zero_drift import probability, volatility


def test_probability_moves_with_spot_and_time():
    assert probability(101,100,600,.0001) > probability(100,100,600,.0001)
    assert probability(101,100,120,.0001) > probability(101,100,600,.0001)
    assert abs(probability(100,100,600,.0001)-.5) < .001
    with pytest.raises(ValueError):
        probability(100,100,30,.0001)


def test_zero_volatility_and_bad_inputs():
    assert probability(100,100,600,0) == 1
    assert probability(99,100,600,0) == 0
    with pytest.raises(ValueError):
        probability(float('nan'),100,600,.001)
    assert volatility([100]*61) == 0


def test_completed_candles_only_and_no_future_leakage():
    rows = [(i*60, i*60+59.999, 100+i*.01) for i in range(100)]
    past = history(rows, 3722)
    changed = [(a,b,999999 if b+2 > 3722 else c) for a,b,c in rows]
    assert past == history(changed,3722)
    assert past[-1] == rows[61][2]
    assert history(rows[:20],3722) is None


def test_score_uses_actual_winner():
    report = summary([dict(status='evaluated', winner=1,
        model_probability=.8, market_probability=.6)])
    assert math.isclose(report['model']['brier'],.04)
    assert math.isclose(report['market']['brier'],.16)


def test_hypothetical_trades_include_fees_and_losses():
    from btc.score import hypothetical_trades
    rows = [dict(status='evaluated', market='m', winner=0, quantity='5',
        model_probability=.8, up_cost_per_share='.65', down_cost_per_share='.4')]
    report = hypothetical_trades(rows)
    assert report['trades'][0]['side'] == 'up'
    assert report['hypothetical_pnl'] == -3.25
