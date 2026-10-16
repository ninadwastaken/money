import math


def summary(rows):
    valid = [r for r in rows if r.get('status') == 'evaluated']
    result = dict(markets=len(valid), predictions=valid,
                  note='Exploratory proxy test; one observation per market, not a profitable strategy claim')
    if not valid:
        return result
    for name in ('model', 'market'):
        predictions = [r[name+'_probability'] for r in valid]
        labels = [r['winner'] for r in valid]
        result[name] = dict(
            brier=sum((p-y)**2 for p,y in zip(predictions, labels))/len(valid),
            log_loss=-sum(y*math.log(max(1e-9,p))+(1-y)*math.log(max(1e-9,1-p))
                          for p,y in zip(predictions,labels))/len(valid))
    result['skipped'] = [r for r in rows if r.get('status') != 'evaluated']
    return result


def hypothetical_trades(rows, threshold=.02):
    trades = []
    for row in rows:
        if row.get('status') != 'evaluated':
            continue
        p = row['model_probability']
        options = [('up', p, float(row['up_cost_per_share'])),
                   ('down', 1-p, float(row['down_cost_per_share']))]
        side, chance, cost = max(options, key=lambda x: x[1]-x[2])
        if chance-cost < threshold:
            continue
        wins = row['winner'] == int(side == 'up')
        trades.append(dict(market=row['market'], side=side, expected_edge=chance-cost,
            hypothetical_spend=float(row['quantity'])*cost,
            hypothetical_pnl=float(row['quantity'])*(int(wins)-cost)))
    return dict(threshold=threshold, trades=trades,
                hypothetical_pnl=sum(t['hypothetical_pnl'] for t in trades),
                note='Same-snapshot taker fills assumed; no latency or actual execution')
