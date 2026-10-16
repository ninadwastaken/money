import json
from pathlib import Path

import httpx


def key(row):
    return (row.get('transaction_hash', row.get('transactionHash')),
            row.get('token_id', row.get('asset')), row['side'],
            row['timestamp'], float(row['price']), float(row['size']))


def main():
    root = Path('data/nfl')
    game = '2026_05_BUF_LA'
    original = json.loads((root / 'trades' / (game + '.json')).read_text())
    condition = original[0]['condition_id']
    legacy, pages, complete = [], [], False
    with httpx.Client(timeout=30) as client:
        for offset in range(0, 10001, 1000):
            response = client.get('https://data-api.polymarket.com/trades', params=dict(
                market=condition, limit=1000, offset=offset, takerOnly='true',
                filterType='TOKENS', filterAmount=.000001))
            response.raise_for_status()
            rows = response.json()
            if not isinstance(rows, list):
                raise ValueError('Unexpected legacy trade response')
            legacy.extend(rows)
            pages.append(len(rows))
            if len(rows) < 1000:
                complete = True
                break
    folder = root / 'history-audit'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (game + '-legacy.json')).write_text(json.dumps(legacy) + '\n')
    old_keys, legacy_keys = set(map(key, original)), set(map(key, legacy))
    report = dict(game=game, original_rows=len(original), legacy_rows=len(legacy),
        legacy_pages=pages, legacy_pagination_exhausted=complete,
        original_not_in_legacy=len(old_keys - legacy_keys),
        legacy_not_in_original=len(legacy_keys - old_keys),
        note='Separate endpoint, same provider; matching histories do not prove on-chain completeness.')
    (folder / 'legacy-comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
