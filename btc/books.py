from decimal import Decimal as D


class Books:
    def __init__(self):
        self.reset()

    def reset(self):
        self.books = {}
        self.updated = {}

    def apply(self, event, received):
        kind = event.get('event_type')
        if kind == 'book':
            asset = event['asset_id']
            self.books[asset] = {
                side: {D(x['price']): D(x['size']) for x in event[side] if D(x['size']) > 0}
                for side in ('bids', 'asks')}
            self.updated[asset] = received
        elif kind == 'price_change':
            for change in event['price_changes']:
                asset = change['asset_id']
                if asset not in self.books:
                    continue
                side = {'BUY': 'bids', 'SELL': 'asks'}[change['side']]
                levels = self.books[asset][side]
                price, size = D(change['price']), D(change['size'])
                if size < 0:
                    raise ValueError('Negative book size')
                if size == 0:
                    levels.pop(price, None)
                else:
                    levels[price] = size
                self.updated[asset] = received
