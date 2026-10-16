import json
from .markets import array


def read(path):
    target, winner, up_asset, rules = None, None, None, None
    for line in path.open():
        if '"kind":"metadata"' not in line and '"kind":"resolution"' not in line:
            continue
        row = json.loads(line)
        event = row['payload']
        market = next(m for m in event['markets'] if m['slug'] == path.parent.name)
        target = event.get('eventMetadata', {}).get('priceToBeat', target)
        outcomes = array(market['outcomes'])
        ids = array(market.get('positionIds') if market.get('version') == 'v2' else market['clobTokenIds'])
        up_asset = ids[outcomes.index('Up')]
        rules = market['description']
        if row['kind'] == 'resolution':
            prices = list(map(float, array(market['outcomePrices'])))
            if sorted(prices) == [0, 1]:
                winner = int(prices[outcomes.index('Up')])
    return dict(target=target, winner=winner, up_asset=up_asset, rules=rules)
