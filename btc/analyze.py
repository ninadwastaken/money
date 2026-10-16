import argparse
import json
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from .pricing import buy_cost
from .replay import frames


def analyze(path, quantity, buffer, max_age):
    stats = Counter()
    best = None
    for books, assets, rate, minimum, now in frames(path, stats):
        if quantity < minimum or len(assets) != 2:
            continue
        if any(a not in books.books or now-books.updated[a] > max_age for a in assets):
            stats['missing_or_stale'] += 1
            continue
        costs = [buy_cost(books.books[a], quantity, rate) for a in assets]
        if any(c is None for c in costs):
            stats['insufficient_depth_or_crossed'] += 1
            continue
        stats['evaluated_updates'] += 1
        margin = quantity-sum(costs)-quantity*buffer
        if best is None or margin > best:
            best = margin
        if margin > 0:
            stats['positive_updates'] += 1
    return dict(market=path.parent.name, quantity_per_side=str(quantity),
                buffer_per_pair=str(buffer), **stats,
                best_pair_margin=str(best) if best is not None else None)


def main():
    parser = argparse.ArgumentParser(description='Replay books and check taker pair economics')
    parser.add_argument('--data', type=Path, default=Path('data'))
    parser.add_argument('--quantity', type=D, default=D('10'))
    parser.add_argument('--buffer', type=D, default=D('.005'), help='Extra cost per pair')
    parser.add_argument('--max-age', type=float, default=3)
    args = parser.parse_args()
    if (not args.quantity.is_finite() or args.quantity <= 0 or
            not args.buffer.is_finite() or args.buffer < 0 or args.max_age <= 0):
        parser.error('Use positive quantity/age and nonnegative buffer')
    paths = sorted(args.data.glob('btc-updown-15m-*/events.jsonl'))
    if not paths:
        parser.error('No recordings found')
    for path in paths:
        print(json.dumps(analyze(path, args.quantity, args.buffer, args.max_age)), flush=True)


if __name__ == '__main__':
    main()
