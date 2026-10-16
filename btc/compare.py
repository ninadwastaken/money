"""Exploratory zero-drift proxy versus recorded odds, five minutes after open."""
import argparse
import json
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from strategies.models.zero_drift import probability, volatility
from .candles import load, history, opening_price
from .outcomes import read
from .pricing import buy_cost
from .replay import frames
from .score import summary, hypothetical_trades


def compare(path, candles):
    info = read(path)
    row = dict(market=path.parent.name, status='missing target or official outcome')
    if info['target'] is None or info['winner'] is None:
        return row
    start = int(path.parent.name.rsplit('-',1)[1])
    decision = start+302  # Completed minute candle plus 2s assumed availability delay.
    for books, assets, rate, minimum, now in frames(path, Counter()):
        if now < decision:
            continue
        if now > decision+3:
            break
        if any(a not in books.books or now-books.updated[a] > 3 for a in assets):
            continue
        prices = history(candles, now)
        if prices is None:
            return dict(row, status='missing completed BTC candles')
        anchor = opening_price(candles, start)
        if anchor is None:
            return dict(row, status='missing Binance opening anchor')
        p = probability(prices[-1], anchor, start+900-now, volatility(prices))
        up = books.books[info['up_asset']]
        if not up['bids'] or not up['asks'] or max(up['bids']) >= min(up['asks']):
            continue
        mid = float((max(up['bids'])+min(up['asks']))/2)
        quantity = max(D('5'), minimum)
        costs = {a: buy_cost(books.books[a],quantity,rate) for a in assets}
        if any(c is None for c in costs.values()):
            continue
        return dict(row, status='evaluated', at=now, winner=info['winner'],
                    model_probability=p, market_probability=mid, quantity=str(quantity),
                    official_target=info['target'], proxy_target=anchor,
                    up_cost_per_share=str(costs[info['up_asset']]/quantity),
                    down_cost_per_share=str(costs[next(a for a in assets if a != info['up_asset'])]/quantity),
                    price_source='Binance return from its own opening anchor; assumes constant feed basis',
                    target_source='Recorded fixed official target, retrospectively recovered')
    return dict(row, status='no fresh synchronized odds at fixed decision time')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candles', type=Path)
    parser.add_argument('--data', type=Path, default=Path('data'))
    args = parser.parse_args()
    candles = load(args.candles)
    rows = []
    for path in sorted(args.data.glob('btc-updown-15m-*/events.jsonl')):
        result = compare(path, candles)
        rows.append(result)
        print(json.dumps(result), flush=True)
    report = summary(rows)
    report["hypothetical_trades"] = hypothetical_trades(rows)
    (args.data/'baseline-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'predictions'}))


if __name__ == '__main__':
    main()
