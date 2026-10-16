import argparse
import json
from pathlib import Path

def download(client, condition, path, *, include_makers=False, minimum_size=0.01):
    manifest_path = path.with_suffix('.manifest.json')
    if path.exists():
        cached = json.loads(manifest_path.read_text()) if manifest_path.exists() else dict(
            include_makers=False, minimum_size=.01, condition=condition)
        if (cached['include_makers'], cached['minimum_size'], cached['condition']) != (
                include_makers, minimum_size, condition):
            raise ValueError('Cached download has different filters; choose another output folder')
        return json.loads(path.read_text())
    rows, cursor, seen = [], None, set()
    pages = []
    while True:
        parameters = dict(condition=condition, limit=1000,
            taker_only=str(not include_makers).lower(), filter_type='TOKENS', filter_amount=minimum_size)
        if cursor:
            parameters['cursor'] = cursor
        response = client.get('https://data-api.polymarket.com/v2/trades', params=parameters)
        response.raise_for_status()
        payload = response.json()
        if any(row.get('condition_id', condition) != condition for row in payload['data']):
            raise ValueError('Response contains a different market')
        pages.append(dict(rows=len(payload['data']), pagination=payload['pagination']))
        rows.extend(payload['data'])
        pagination = payload['pagination']
        if not pagination['has_more']:
            break
        following = pagination['next_cursor']
        if not following or following in seen:
            raise ValueError('Trade pagination did not advance')
        seen.add(following)
        cursor = following
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.part')
    temporary.write_text(json.dumps(rows) + '\n')
    temporary.replace(path)
    manifest_path.write_text(json.dumps(dict(condition=condition,
        include_makers=include_makers, minimum_size=minimum_size, complete_api_pagination=True,
        rows=len(rows), pages=pages), indent=2) + '\n')
    return rows


def main():
    parser = argparse.ArgumentParser(description='Download historical NFL moneyline fills.')
    parser.add_argument('--markets', type=Path, default=Path('data/nfl/defense-screen'))
    parser.add_argument('--output', type=Path, default=Path('data/nfl/trades'))
    parser.add_argument('--plays', type=Path, default=Path('data/nfl/play_by_play_2026.parquet'))
    parser.add_argument('--since', default='2026-01-01')
    parser.add_argument('--include-makers', action='store_true')
    parser.add_argument('--minimum-size', type=float, default=0.01)
    arguments = parser.parse_args()
    if arguments.minimum_size <= 0:
        parser.error('--minimum-size must be positive; zero restores the API default')
    from nfl.season_trades import run
    run(arguments.plays, arguments.since, arguments.markets, arguments.output,
        include_makers=arguments.include_makers, minimum_size=arguments.minimum_size)


if __name__ == '__main__':
    main()
