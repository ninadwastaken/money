"""Fixed-baseline, one-prediction-per-round historical comparison."""
import json
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from strategies.models.zero_drift import probability, volatility
from .candles import load, history, opening_price
from .historical_results import parse, ROOT
from .score import summary, hypothetical_trades
from .evidence import assess


def compare(slug, quotes, candles):
    official = ROOT/'official'/(slug+'.json')
    row = dict(market=slug,status='missing official outcome')
    if not official.exists():
        return row
    result = parse(json.loads(official.read_text()),slug)
    start = int(slug.rsplit('-',1)[1])
    now = start+302
    prices, anchor = history(candles,now), opening_price(candles,start)
    if prices is None or anchor is None:
        return dict(row,status='missing completed candles')
    p = probability(prices[-1],anchor,598,volatility(prices),result['averaging_seconds'])
    costs = {}
    for side in ('up','down'):
        ask = D(str(quotes[side]['best_ask']))
        costs[side] = str(ask+D('.07')*ask*(1-ask))
    return dict(row,status='evaluated',at=now,winner=result['winner'],
        model_probability=p,market_probability=(quotes['up']['best_bid']+quotes['up']['best_ask'])/2,
        quantity='5',up_cost_per_share=costs['up'],down_cost_per_share=costs['down'],
        averaging_seconds=result['averaging_seconds'])


def main():
    quotes = json.loads((ROOT/'quotes.json').read_text())
    candles = sorted(r for p in ROOT.glob('BTCUSDT-1m-*.zip') for r in load(p))
    rows = [compare(slug,q,candles) for slug,q in sorted(quotes.items())]
    report = summary(rows)
    report['hypothetical_trades'] = hypothetical_trades(rows)
    report['uncertainty'] = assess(rows)
    report['method'] = dict(decision='302s after open',quote_max_age_seconds=3,
        price_source='Binance own-open-relative minute-close proxy',volatility='60 minutes EWMA .94',
        costs='Illustrative current 0.07 fee coefficient; historical fee schedule unverified',
        execution='Top-of-book quote-only; depth and latency unverified, not executable P&L',
        labels='Official Gamma resolved outcomes',selection='Coverage-based dates, no model tuning')
    days = {}
    for row in rows:
        if row['status'] != 'evaluated':
            continue
        from datetime import datetime, timezone
        day = datetime.fromtimestamp(row['at'],timezone.utc).date().isoformat()
        days.setdefault(day,[]).append(row)
    report['by_day'] = {day:{k:v for k,v in summary(values).items()
                             if k not in ('predictions','skipped')} for day,values in days.items()}
    (ROOT/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('predictions','skipped','hypothetical_trades')},indent=2))
    trades = report['hypothetical_trades']
    print('Illustrative trades:',len(trades['trades']),'quote-only P&L:',trades['hypothetical_pnl'])


if __name__ == '__main__':
    main()
