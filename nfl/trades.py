import argparse
import json
from pathlib import Path

def download(client, condition, path):
    if path.exists():
        return json.loads(path.read_text())
    rows, cursor = [], None
    while True:
        parameters = dict(condition=condition, limit=1000, taker_only='true')
        if cursor:
            parameters['cursor'] = cursor
        response = client.get('https://data-api.polymarket.com/v2/trades', params=parameters)
        response.raise_for_status()
        payload = response.json()
        rows.extend(payload['data'])
        pagination = payload['pagination']
        if not pagination['has_more']:
            break
        following = pagination['next_cursor']
        if not following or following == cursor:
            raise ValueError('Trade pagination did not advance')
        cursor = following
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows) + '\n')
    return rows


def main():
    parser = argparse.ArgumentParser(description='Download historical NFL moneyline fills.')
    parser.add_argument('--markets', type=Path, default=Path('data/nfl/defense-screen'))
    parser.add_argument('--output', type=Path, default=Path('data/nfl/trades'))
    parser.add_argument('--plays', type=Path, default=Path('data/nfl/play_by_play_2026.parquet'))
    parser.add_argument('--since', default='2026-01-01')
    arguments = parser.parse_args()
    from nfl.season_trades import run
    run(arguments.plays, arguments.since, arguments.markets, arguments.output)


if __name__ == '__main__':
    main()
