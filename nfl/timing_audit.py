import argparse
from collections import Counter
import json
from pathlib import Path

from nfl.fixed_windows import fixed_windows
from nfl.possessions import games


def main():
    parser = argparse.ArgumentParser(description='Check data readiness for fixed NFL holds.')
    parser.add_argument('--plays', default='data/nfl/play_by_play_2026.parquet')
    parser.add_argument('--since', default='2026-10-11')
    parser.add_argument('--output', default='data/nfl/fixed-timing/audit.json')
    arguments = parser.parse_args()
    grouped = games(arguments.plays, arguments.since)
    candidates = [window for plays in grouped.values() for window in fixed_windows(plays)]
    counts = Counter(f"{row['entry_delay']}s to {row['exit_delay']}s" for row in candidates)
    report = dict(
        status='blocked by data precision; no returns calculated',
        games=len(grouped), candidates_by_rule=dict(counts),
        usable_executable_trades=0,
        missing=[
            'Verified timestamps for when each team actually starts defending',
            'Timestamped bid/ask prices and available sizes at entry and exit',
            'Historical fees and execution delay for each market',
        ],
        rules='Hold until the fixed exit, including scores and possession changes.',
        validation='Select rules on earlier games; evaluate once on later games.',
        candidates=candidates,
    )
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'candidates'}, indent=2))


if __name__ == '__main__':
    main()
