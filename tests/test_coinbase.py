import asyncio
import json
from unittest.mock import patch
from btc.coinbase import session, record, CHANNELS
from btc.coinbase_quality import Quality
from btc.storage import Storage


def test_trade_gaps_duplicates_and_heartbeat():
    q = Quality()
    assert q.observe(dict(type='last_match',trade_id=10)) is None
    assert q.observe(dict(type='match',trade_id=11)) is None
    assert q.observe(dict(type='match',trade_id=11))[0] == 'duplicate_trade'
    assert q.observe(dict(type='match',trade_id=13))[0] == 'trade_gap'
    assert q.observe(dict(type='heartbeat',last_trade_id=14)) is None
    assert q.observe(dict(type='heartbeat',last_trade_id=14))[0] == 'trade_gap'


def test_snapshot_required_and_subscription_errors():
    import pytest
    q = Quality()
    with pytest.raises(ValueError):
        q.observe(dict(type='l2update'))
    assert q.observe(dict(type='snapshot'))[0] == 'synced'
    assert q.observe(dict(type='l2update')) is None
    with pytest.raises(ValueError):
        q.observe(dict(type='error',message='bad subscription'))


def test_stream_preserves_raw_snapshot_and_trades(tmp_path):
    sent, done = [], asyncio.Event()
    messages = [dict(type='snapshot',product_id='BTC-USD',bids=[['100','2']],asks=[['101','3']]),
                dict(type='last_match',trade_id=10),dict(type='match',trade_id=11,side='sell')]
    class Socket:
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def send(self,value): sent.append(json.loads(value))
        async def recv(self):
            if messages: return json.dumps(messages.pop(0))
            done.set()
            await asyncio.Future()
    async def check():
        store = Storage(tmp_path,'feed')
        with patch('btc.coinbase.connect',return_value=Socket()):
            task = asyncio.create_task(session(store))
            await asyncio.wait_for(done.wait(),1)
            task.cancel()
            await asyncio.gather(task,return_exceptions=True)
        store.close()
    asyncio.run(check())
    assert sent[0]['channels'] == CHANNELS
    rows = [json.loads(x) for x in (tmp_path/'feed/events.jsonl').read_text().splitlines()]
    assert [r['kind'] for r in rows] == ['connection','ws','synced','ws','ws']
    assert json.loads(rows[-1]['payload'])['side'] == 'sell'


def test_recorder_cancellation_flushes_stop(tmp_path):
    entered = asyncio.Event()
    async def idle(store):
        entered.set()
        await asyncio.Future()
    async def check():
        with patch('btc.coinbase.session',idle):
            task = asyncio.create_task(record(tmp_path))
            await entered.wait()
            task.cancel()
            await asyncio.gather(task,return_exceptions=True)
    asyncio.run(check())
    rows = (tmp_path/'coinbase-btc-usd/events.jsonl').read_text().splitlines()
    assert json.loads(rows[-1])['kind'] == 'stop'
