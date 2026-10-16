import json
from datetime import datetime
from decimal import Decimal as D
from .markets import array
from .books import Books


def frames(path, stats):
    books, previous = Books(), None
    assets, rate, end, minimum = (), None, 0, D(0)
    with path.open() as source:
        for line in source:
            stats['records'] += 1
            row = json.loads(line)
            run = row['run']
            if previous and (run != previous[0] or row['sequence'] != previous[1]+1):
                books.reset()
                stats['sequence_breaks'] += 1
            previous = run, row['sequence']
            kind, payload = row['kind'], row['payload']
            if kind in ('connection', 'gap', 'stop'):
                books.reset()
                stats[kind] += 1
            elif kind == 'metadata':
                market = next(m for m in payload['markets'] if m['slug'] == path.parent.name)
                key = 'positionIds' if market.get('version') == 'v2' else 'clobTokenIds'
                assets = tuple(array(market[key]))
                schedule = market['feeSchedule']
                if schedule['exponent'] != 1 or not schedule['takerOnly']:
                    raise ValueError('Unsupported fee schedule')
                rate = D(str(schedule['rate'])) if market['feesEnabled'] else D(0)
                minimum = D(str(market['orderMinSize']))
                end = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00')).timestamp()
            elif kind == 'ws':
                received = row['received_ns']/1e9
                messages = json.loads(payload)
                for event in messages if isinstance(messages, list) else [messages]:
                    books.apply(event, received)
                if assets and received < end:
                    yield books, assets, rate, minimum, received
