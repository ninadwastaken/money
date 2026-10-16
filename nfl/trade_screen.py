import argparse
import json
from pathlib import Path

from nfl.fixed_windows import TIMINGS, fixed_windows
from nfl.possessions import games
from nfl.teams import NAMES
from nfl.trade_prices import screen, trade_series


def run(plays_path, since, data, output, maximum_age):
    results = []
    for game, plays in games(plays_path, since).items():
        rows = json.loads((data / 'trades' / (game + '.json')).read_text())
        event = json.loads((data / 'defense-screen' / (game + '-market.json')).read_text())
        market = next(row for row in event['markets'] if row.get('sportsMarketType') == 'moneyline')
        tokens = dict(zip(json.loads(market['outcomes']), json.loads(market['clobTokenIds'])))
        rate = market['feeSchedule']['rate'] if market.get('feesEnabled') else 0
        if rate and market['feeSchedule']['exponent'] != 1:
            raise ValueError('Unsupported fee exponent')
        series = {team: (trade_series(rows, token, 'BUY'), trade_series(rows, token, 'SELL'))
                  for team, token in tokens.items()}
        for window in fixed_windows(plays):
            buys, sells = series[NAMES[window['team']]]
            results.append(screen(window, buys, sells, rate, maximum_age))
    summaries = []
    for entry, exit_delay in TIMINGS:
        candidates = [row for row in results if row['entry_delay'] == entry and row['exit_delay'] == exit_delay]
        usable = [row for row in candidates if row['status'] == 'screened']
        summaries.append(dict(entry_seconds=entry, exit_seconds=exit_delay, candidates=len(candidates),
            screened=len(usable), games=len({row['game'] for row in usable}),
            mean_raw_change_cents=sum(row['raw_change_cents'] for row in usable)/len(usable) if usable else None,
            hypothetical_profit=sum(row['hypothetical_profit'] for row in usable),
            positive=sum(row['hypothetical_profit'] > 0 for row in usable)))
    report = dict(status='Exploratory trade-price screen, not executable returns',
        maximum_trade_age_seconds=maximum_age, stake_per_position=10, summaries=summaries,
        limitations=['Drive starts are proxies for possession acquisition.',
            'On-chain timestamps are not quote availability timestamps; same-second fills use volume-weighted prices.',
            'Past BUY/SELL fills do not establish available bid/ask prices or liquidity for our orders.',
            'Fees use current cached metadata; execution delay and slippage are not modeled.',
            'Missing pairs are excluded; sparse coverage can bias results. No held-out validation.'], results=results)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'results'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--since', default='2026-10-11')
    parser.add_argument('--maximum-age', type=int, default=5)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run('data/nfl/play_by_play_2026.parquet', args.since, Path('data/nfl'),
        args.output or Path(f'data/nfl/fixed-timing/trade-screen-{args.maximum_age}s.json'), args.maximum_age)
