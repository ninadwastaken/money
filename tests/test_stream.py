import asyncio
import json
from unittest.mock import patch
from btc.markets import Market
from btc.storage import Storage
from btc.stream import session


def test_snapshots_precede_synced_and_raw_updates_survive(tmp_path):
    messages = [json.dumps([
        dict(event_type='book', asset_id='u', bids=[], asks=[]),
        dict(event_type='book', asset_id='d', bids=[], asks=[]),
    ]), json.dumps(dict(event_type='price_change', timestamp='123',
                        price_changes=[dict(asset_id='u', price='.4', size='5', side='BUY')]))]
    done = asyncio.Event()
    class Socket:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def send(self, message):
            pass
        async def recv(self):
            if messages:
                return messages.pop(0)
            done.set()
            await asyncio.Future()
    async def check():
        store = Storage(tmp_path, 'btc')
        with patch('btc.stream.connect', return_value=Socket()):
            task = asyncio.create_task(session(Market('btc', ('u','d'), 'c', {}), store))
            await asyncio.wait_for(done.wait(), 1)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        store.close()
    asyncio.run(check())
    rows = [json.loads(x) for x in (tmp_path/'btc/events.jsonl').read_text().splitlines()]
    assert [x['kind'] for x in rows] == ['connection', 'ws', 'synced', 'ws']
    assert json.loads(rows[-1]['payload'])['price_changes'][0]['size'] == '5'
