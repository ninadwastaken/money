import json

from nfl import season_trades


def test_missing_market_does_not_stop_other_games(monkeypatch, tmp_path):
    play = dict(time_of_day='2026-09-10T20:00:00Z', end_clock_time='2026-09-10T23:00:00Z')
    monkeypatch.setattr(season_trades, 'games', lambda *_: {'missing': [play], 'found': [play]})

    def market(client, plays, folder):
        if getattr(market, 'called', False):
            raise ValueError('No matching market')
        market.called = True
        return dict(conditionId='condition')

    monkeypatch.setattr(season_trades, 'fetch_market', market)
    monkeypatch.setattr(season_trades, 'download', lambda *_: [dict(timestamp=1790000000)])
    report = season_trades.run('plays', '2026-01-01', tmp_path / 'markets', tmp_path / 'trades')
    assert report['games'] == 2
    assert [row['status'] for row in report['coverage']] == ['no in-game trades', 'error']
    assert json.loads((tmp_path / 'trades' / 'coverage.json').read_text()) == report
