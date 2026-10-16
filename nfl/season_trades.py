from datetime import datetime, timezone
import json

import httpx

from nfl.possessions import games, timestamp
from nfl.prices import fetch_market
from nfl.trades import download


def run(plays_path, since, markets, output):
    markets.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    coverage = []
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        for game, plays in sorted(games(plays_path, since).items()):
            result = dict(game=game)
            try:
                market = fetch_market(client, plays, markets)
                rows = download(client, market['conditionId'], output / (game + '.json'))
                start = min(timestamp(p['time_of_day']) for p in plays if p['time_of_day'])
                end = max(timestamp(p['end_clock_time'] or p['time_of_day']) or 0 for p in plays)
                in_game = sum(start <= row['timestamp'] <= end for row in rows)
                result.update(status='downloaded' if in_game else 'no in-game trades',
                              condition=market['conditionId'], trades=len(rows), in_game_trades=in_game)
            except (httpx.HTTPError, ValueError, KeyError, StopIteration) as error:
                result.update(status='error', error=f'{type(error).__name__}: {error}')
            coverage.append(result)
            print(game, result, flush=True)
    report = dict(downloaded_at=datetime.now(timezone.utc).isoformat(), plays=str(plays_path),
        source='https://data-api.polymarket.com/v2/trades', since=since,
        games=len(coverage), games_with_in_game_trades=sum(row.get('in_game_trades', 0) > 0 for row in coverage),
        trades=sum(row.get('trades', 0) for row in coverage),
        in_game_trades=sum(row.get('in_game_trades', 0) for row in coverage), coverage=coverage)
    (output / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'coverage'}, indent=2))
    return report
