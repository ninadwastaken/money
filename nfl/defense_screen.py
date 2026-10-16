from collections import Counter
import argparse
import json
from pathlib import Path

from nfl.defense_windows import defense_windows
from nfl.band_prices import band_screen
from nfl.entry_clock import entry_allowed
from nfl.possessions import games
from nfl.teams import NAMES
from nfl.trade_prices import screen, trade_series


def run(cutoff=0, bands=False):
    data = Path('data/nfl')
    results = []
    for game, plays in games(data / 'play_by_play_2026.parquet', '2026-01-01').items():
        rows = json.loads((data / 'trades' / (game + '.json')).read_text())
        event = json.loads((data / 'defense-screen' / (game + '-market.json')).read_text())
        market = next(row for row in event['markets'] if row.get('sportsMarketType') == 'moneyline')
        names = json.loads(market['outcomes'])
        tokens = dict(zip(names, json.loads(market['clobTokenIds'])))
        payouts = dict(zip(names, map(float, json.loads(market['outcomePrices']))))
        rate = market['feeSchedule']['rate'] if market.get('feesEnabled') else 0
        if rate and market['feeSchedule']['exponent'] != 1:
            raise ValueError('Unsupported fee exponent')
        if not market.get('closed') or market.get('umaResolutionStatus') != 'resolved':
            raise ValueError(f'{game} has no verified settlement')
        series = {name: (trade_series(rows, token, 'BUY'), trade_series(rows, token, 'SELL'))
                  for name, token in tokens.items()}
        for window in defense_windows(plays):
            if cutoff and not bands and not entry_allowed(plays, window['entry_time'], cutoff):
                results.append(dict(window, status='late-game cutoff or unknown clock'))
                continue
            name = NAMES[window['team']]
            buys, sells = series[name]
            if bands:
                results.append(band_screen(window, buys, sells, rate, plays, cutoff,
                    payout=payouts[name] if window['settlement'] else None))
                continue
            results.append(screen(window, buys, sells, rate,
                payout=payouts[name] if window['settlement'] else None))
    usable = [row for row in results if row['status'] == 'screened']
    rule = ('First BUY fill 20-40s after defense starts; first SELL fill 0-20s after return to offense'
            if bands else 'Buy defense start +30 seconds; sell when the same team returns to offense')
    report = dict(rule=rule,
        status='Exploratory trade-price screen, not executable returns', stake=10, maximum_trade_age_seconds=5,
        cutoff_seconds=cutoff, bands=bands, candidates=len(results), statuses=dict(Counter(row['status'] for row in results)),
        games_with_usable_entries=len({row['game'] for row in usable}),
        hypothetical_profit=sum(row['hypothetical_profit'] for row in usable),
        positive=sum(row['hypothetical_profit'] > 0 for row in usable),
        settlement_entries=sum(row['settlement'] for row in usable),
        limitations=['Both possession switches use first offensive play/drive-start proxies, possibly after commercials.',
            'Cutoff conservatively subtracts wall time since last observed play clock; no overtime entries with cutoff.',
            'Completed trades are not executable quotes; no order delay, slippage or liquidity modeled.',
            'Uses current cached fees and block timestamps. Missing pairs excluded; no held-out validation.',
            'Final defensive possessions held to official settlement if the team never regains possession.'],
        results=results)
    report['maximum_trade_age_seconds'] = None if bands else 5
    output = data / 'defense-return' / (f'bands-cutoff-{cutoff}s.json' if bands else
                                      f'screen-cutoff-{cutoff}s.json' if cutoff else 'screen.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'results'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cutoff', type=int, default=0)
    parser.add_argument('--bands', action='store_true')
    args = parser.parse_args()
    if args.cutoff < 0:
        parser.error('--cutoff must be nonnegative')
    run(args.cutoff, args.bands)
