from decimal import Decimal as D, ROUND_HALF_UP


def buy_cost(book, quantity, rate):
    remaining, total = quantity, D(0)
    if book['bids'] and book['asks'] and max(book['bids']) >= min(book['asks']):
        return None
    for price, size in sorted(book['asks'].items()):
        if not 0 < price < 1:
            return None
        take = min(remaining, size)
        fee = (take * rate * price * (1-price)).quantize(D('.00001'), rounding=ROUND_HALF_UP)
        total += take*price + fee
        remaining -= take
        if not remaining:
            return total
    return None
