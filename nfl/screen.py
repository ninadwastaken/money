import argparse
import json
from pathlib import Path
import httpx
from .possessions import games, windows, timestamp
from .prices import fetch_market, fetch_history
from .price_screen import observations, evaluate
from .teams import NAMES


def run(path, since, delay, folder):
    folder.mkdir(parents=True,exist_ok=True)
    results, errors = [], []
    with httpx.Client(follow_redirects=True,timeout=30) as client:
        for game,plays in games(path,since).items():
            try:
                market = fetch_market(client,plays,folder)
                tokens = json.loads(market['clobTokenIds'])
                names = json.loads(market['outcomes'])
                payouts = list(map(float,json.loads(market['outcomePrices'])))
                if not market.get('closed') or market.get('umaResolutionStatus')!='resolved':
                    raise ValueError('Game not officially resolved')
                start = min(timestamp(p['time_of_day']) for p in plays if p['time_of_day'])
                end = max(timestamp(p['end_clock_time'] or p['time_of_day']) or 0 for p in plays)
                histories = {name:observations(fetch_history(client,token,start-120,end+120,
                    folder/(game+'-'+name+'.json'))) for name,token in zip(names,tokens)}
                rate = market['feeSchedule']['rate'] if market.get('feesEnabled') else 0
                if market.get('feesEnabled') and market['feeSchedule']['exponent']!=1:
                    raise ValueError('Unsupported fee formula')
                for window in windows(plays,delay):
                    name = NAMES[window['team']]
                    result = evaluate(window,histories[name],payouts[names.index(name)],rate)
                    results.append(result)
                print(game,'windows',len(windows(plays,delay)),flush=True)
            except (httpx.HTTPError,KeyError,ValueError,StopIteration) as error:
                errors.append(dict(game=game,error=str(error)))
                print(game,str(error),flush=True)
    screened = [r for r in results if r['status']=='screened']
    report = dict(delay_seconds=delay,screened=len(screened),windows=len(results),errors=errors,
        mean_change_cents=sum(r['change_cents'] for r in screened)/len(screened) if screened else None,
        mean_fee_adjusted_change_cents=sum(r['fee_adjusted_change_cents'] for r in screened)/len(screened) if screened else None,
        note='Chart-price screen only, not executable P&L. Drive-start/exit timing are proxies; '
             'bucket availability assumed at bucket end. No bid/ask, size or feed-latency history.',
        results=results)
    (folder/'screen.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Screen delayed defensive moneyline entries')
    parser.add_argument('--plays',type=Path,default=Path('data/nfl/play_by_play_2026.parquet'))
    parser.add_argument('--since',default='2026-10-11')
    parser.add_argument('--delay',type=int,default=60)
    parser.add_argument('--output',type=Path,default=Path('data/nfl/defense-screen'))
    args = parser.parse_args()
    if args.delay<0:
        parser.error('--delay cannot be negative')
    run(args.plays,args.since,args.delay,args.output)
