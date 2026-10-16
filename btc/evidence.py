"""Day-block uncertainty for fixed historical comparisons."""
import random
from datetime import datetime, timezone
from .score import hypothetical_trades


def day_key(row):
    return datetime.fromtimestamp(row['at'],timezone.utc).date().isoformat()


def assess(rows, repeats=5000, seed=42):
    days = {}
    for row in rows:
        if row.get('status') == 'evaluated':
            days.setdefault(day_key(row),[]).append(row)
    if not days:
        return {'days': 0}
    blocks = []
    details = {}
    for day, values in sorted(days.items()):
        trades = hypothetical_trades(values)
        difference = sum((r['market_probability']-r['winner'])**2-
                         (r['model_probability']-r['winner'])**2 for r in values)
        block = (len(values),difference,trades['hypothetical_pnl'])
        blocks.append(block)
        details[day] = dict(rounds=block[0],brier_improvement=block[1]/block[0],
                            trades=len(trades['trades']),hypothetical_pnl=block[2])
    rng, improvements, profits = random.Random(seed), [], []
    for _ in range(repeats):
        sample = rng.choices(blocks,k=len(blocks))
        improvements.append(sum(b[1] for b in sample)/sum(b[0] for b in sample))
        profits.append(sum(b[2] for b in sample)/len(sample))
    def interval(values):
        values.sort()
        return [values[int(.025*repeats)],values[int(.975*repeats)]]
    return dict(days=len(days),by_day=details,
        brier_improvement_ci95=interval(improvements),
        hypothetical_daily_pnl_ci95=interval(profits),
        positive_days=sum(b[2]>0 for b in blocks),
        note='Exploratory day-block bootstrap; coverage gaps, regime dependence and execution assumptions remain')
