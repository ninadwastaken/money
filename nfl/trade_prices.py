from bisect import bisect_right


def trade_series(rows, token, side):
    grouped = {}
    for row in rows:
        if row['token_id'] != token or row['side'] != side:
            continue
        at = int(row['timestamp'])
        cash, shares = grouped.get(at, (0, 0))
        grouped[at] = (cash + float(row['price']) * float(row['size']),
                       shares + float(row['size']))
    return sorted((at, cash / shares) for at, (cash, shares) in grouped.items() if shares > 0)


def recent_trade(series, at, maximum_age):
    index = bisect_right(series, (at, float('inf'))) - 1
    if index < 0 or at - series[index][0] > maximum_age:
        return None
    return series[index]


def screen(window, buys, sells, fee_rate, maximum_age=5, stake=10, payout=None):
    if window['entry_time'] >= window['exit_time']:
        return dict(window, status='possession ended before entry')
    entry = recent_trade(buys, window['entry_time'], maximum_age)
    exit_trade = ((window['exit_time'], payout) if payout is not None else
                  recent_trade(sells, window['exit_time'], maximum_age))
    if entry is None or exit_trade is None:
        return dict(window, status='missing recent trade')
    entry_at, entry_price = entry
    exit_at, exit_price = exit_trade
    if not 0 < entry_price < 1 or exit_at <= entry_at:
        return dict(window, status='invalid trade pair')
    buy_fee = fee_rate * entry_price * (1 - entry_price)
    sell_fee = fee_rate * exit_price * (1 - exit_price) if payout is None else 0
    shares = stake / (entry_price + buy_fee)
    return dict(window, status='screened', entry_trade_time=entry_at,
                exit_trade_time=exit_at, entry_price=entry_price, exit_price=exit_price,
                raw_change_cents=100 * (exit_price - entry_price),
                hypothetical_profit=shares * (exit_price - sell_fee) - stake)
