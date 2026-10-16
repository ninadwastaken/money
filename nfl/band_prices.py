from bisect import bisect_left

from nfl.entry_clock import entry_allowed
from nfl.trade_prices import screen


def first_trade(series, start, end):
    index = bisect_left(series, (start, -1))
    return series[index] if index < len(series) and series[index][0] <= end else None


def band_screen(window, buys, sells, rate, plays, cutoff, payout=None):
    start = window['defense_start_proxy']
    entry = first_trade(buys, start + 20, start + 40)
    if start + 20 >= window['exit_time']:
        return dict(window, status='possession ended before entry')
    if entry is None:
        return dict(window, status='missing entry trade in 20-40s')
    if entry[0] >= window['exit_time']:
        return dict(window, status='possession ended before entry')
    if not entry_allowed(plays, entry[0], cutoff):
        return dict(window, status='late-game cutoff or unknown clock')
    exit_trade = ((window['exit_time'], payout) if payout is not None else
                  first_trade(sells, window['exit_time'], window['exit_time'] + 20))
    if exit_trade is None:
        return dict(window, status='missing exit trade in 0-20s', entry_trade_time=entry[0])
    selected = dict(window, entry_time=entry[0], exit_time=exit_trade[0],
                    offense_start_proxy=window['exit_time'])
    return screen(selected, [entry], [exit_trade], rate, maximum_age=0, payout=payout)
