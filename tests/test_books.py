from decimal import Decimal as D
from btc.books import Books
from btc.pricing import buy_cost


def test_absolute_updates_deletion_and_reset():
    books = Books()
    books.apply(dict(event_type='book', asset_id='u', bids=[],
                     asks=[dict(price='.5', size='10')]), 1)
    def change(size):
        return dict(event_type='price_change', price_changes=[
            dict(asset_id='u', side='SELL', price='.5', size=size)])
    books.apply(change('3'), 2)
    assert books.books['u']['asks'][D('.5')] == 3
    books.apply(change('0'), 3)
    assert not books.books['u']['asks']
    books.reset()
    books.apply(change('8'), 4)
    assert not books.books


def test_fees_depth_and_crossed_books():
    book = {'bids': {}, 'asks': {D('.5'): D('5'), D('.6'): D('5')}}
    assert buy_cost(book, D('10'), D('.07')) == D('5.67150')
    assert buy_cost(book, D('11'), D('.07')) is None
    book['bids'][D('.7')] = D('10')
    assert buy_cost(book, D('1'), D('.07')) is None


def test_replay_waits_for_books_after_gap(tmp_path):
    import json
    from collections import Counter
    from btc.replay import frames
    folder = tmp_path/'btc-updown-15m-0'
    folder.mkdir()
    metadata = {'markets': [dict(slug=folder.name, clobTokenIds='["u","d"]',
        feeSchedule=dict(exponent=1, takerOnly=True, rate=.07), feesEnabled=True,
        orderMinSize=5, endDate='2030-01-01T00:00:00Z')]}
    book = dict(event_type='book', asset_id='u', bids=[], asks=[dict(price='.5', size='10')])
    change = dict(event_type='price_change', price_changes=[
        dict(asset_id='u', side='SELL', price='.4', size='10')])
    rows = [('metadata', metadata), ('ws', json.dumps(book)), ('gap', {}),
            ('ws', json.dumps(change))]
    path = folder/'events.jsonl'
    path.write_text(''.join(json.dumps(dict(run='a', sequence=i, received_ns=i*10**9,
        kind=kind, payload=payload))+'\n' for i,(kind,payload) in enumerate(rows, 1)))
    snapshots = [dict(b.books) for b,*_ in frames(path, Counter())]
    assert 'u' in snapshots[0]
    assert snapshots[1] == {}

