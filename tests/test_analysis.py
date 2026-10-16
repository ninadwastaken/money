from decimal import Decimal as D


def test_analyzer_detects_profitable_pair(tmp_path):
    import json
    from btc.analyze import analyze
    folder = tmp_path/'btc-updown-15m-0'
    folder.mkdir()
    metadata = {'markets': [dict(slug=folder.name, clobTokenIds='["u","d"]',
        feeSchedule=dict(exponent=1, takerOnly=True, rate=.07), feesEnabled=True,
        orderMinSize=5, endDate='2030-01-01T00:00:00Z')]}
    books = [dict(event_type='book', asset_id=a, bids=[],
                  asks=[dict(price='.45', size='10')]) for a in ('u', 'd')]
    path = folder/'events.jsonl'
    rows = [('metadata', metadata), ('ws', json.dumps(books))]
    path.write_text(''.join(json.dumps(dict(run='a', sequence=i, received_ns=i*10**9,
        kind=kind, payload=payload))+'\n' for i,(kind,payload) in enumerate(rows,1)))
    result = analyze(path, D('10'), D('.005'), 3)
    assert result['positive_updates'] == 1
    assert D(result['best_pair_margin']) == D('.60350')
