"""Detect incomplete public trade data without assuming filtered sequence continuity."""


class Quality:
    def __init__(self):
        self.ready = False
        self.last_trade = None
        self.heartbeat_trade = None

    def observe(self, event):
        kind = event['type']
        if kind == 'error':
            raise ValueError(event.get('message','Coinbase subscription error'))
        if kind == 'snapshot':
            self.ready = True
            return 'synced', {'product': 'BTC-USD', 'scope': 'order_book'}
        if kind == 'l2update' and not self.ready:
            raise ValueError('Book update before snapshot')
        if kind in ('last_match','match'):
            trade = event['trade_id']
            previous = self.last_trade
            if previous is not None and trade <= previous:
                return 'duplicate_trade', {'trade_id': trade, 'previous': previous}
            self.last_trade = trade
            if kind == 'match' and previous is not None and trade > previous+1:
                return 'trade_gap', {'after': previous, 'before': trade}
        if kind == 'heartbeat':
            previous = self.heartbeat_trade
            self.heartbeat_trade = event['last_trade_id']
            if previous is not None and (self.last_trade is None or previous > self.last_trade):
                return 'trade_gap', {'last_received': self.last_trade, 'missing_through': previous}
        return None
