import json
from pathlib import Path

from nfl.audit_history import key


def main():
    root = Path('data/nfl')
    coverage = json.loads((root / 'trades-all' / 'coverage.json').read_text())
    games = []
    for item in coverage['coverage']:
        if item['status'] == 'error':
            continue
        game = item['game']
        original = json.loads((root / 'trades' / (game + '.json')).read_text())
        expanded = json.loads((root / 'trades-all' / (game + '.json')).read_text())
        original_keys = set(map(key, original))
        expanded_keys = set(map(key, expanded))
        original_times = {row['timestamp'] for row in original}
        expanded_times = {row['timestamp'] for row in expanded}
        games.append(dict(game=game, original_records=len(original), expanded_records=len(expanded),
            original_records_not_found=len(original_keys - expanded_keys),
            added_active_seconds=len(expanded_times - original_times)))
    report = dict(games=len(games), original_records=sum(row['original_records'] for row in games),
        expanded_records=sum(row['expanded_records'] for row in games),
        original_records_not_found=sum(row['original_records_not_found'] for row in games),
        added_active_seconds=sum(row['added_active_seconds'] for row in games),
        note='Maker rows add participant perspectives; record counts are not distinct fills. '
             'Exhausted API pagination does not establish independent on-chain completeness.', coverage=games)
    folder = root / 'history-audit'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'expanded-comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'coverage'}, indent=2))


if __name__ == '__main__':
    main()
