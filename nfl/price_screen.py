from bisect import bisect_right


def observations(points):
    result = []
    for point in points:
        width = point['resolution_seconds']
        if width not in (0,60):
            continue
        result.append((float(point['timestamp'])+width,float(point['price'])))
    return sorted(result)


def asof(points, at):
    index = bisect_right(points,(at,float('inf')))-1
    if index < 0 or at-points[index][0] > 60:
        return None
    price = points[index][1]
    return price if 0 < price < 1 else None


def evaluate(window, points, settlement_price, fee_rate):
    entry = asof(points,window['entry_time'])
    exit_price = settlement_price if window['settlement'] else asof(points,window['exit_time'])
    if entry is None or exit_price is None:
        return dict(window,status='missing usable price')
    fee = fee_rate*entry*(1-entry)
    if not window['settlement']:
        fee += fee_rate*exit_price*(1-exit_price)
    return dict(window,status='screened',entry_price=entry,exit_price=exit_price,
                change_cents=100*(exit_price-entry),
                fee_adjusted_change_cents=100*(exit_price-entry-fee))
