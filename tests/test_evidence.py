from btc.evidence import assess


def test_day_blocks_keep_all_rounds_together():
    rows = [dict(status='evaluated',at=day,market=str(day),winner=1,
        model_probability=.8,market_probability=.6,quantity='5',
        up_cost_per_share='.7',down_cost_per_share='.4') for day in (86400,172800)]
    result = assess(rows,repeats=100)
    assert result['days'] == 2
    assert result['positive_days'] == 2
    assert abs(result['brier_improvement_ci95'][0]-.12) < 1e-9
    assert result['hypothetical_daily_pnl_ci95'][0] > 0
    assert assess([]) == {'days':0}
