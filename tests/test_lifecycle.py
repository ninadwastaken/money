import asyncio
import json
from unittest.mock import patch
from btc.lifecycle import watch
from btc.markets import Market


def test_resolution_stops_stream_and_closes_file(tmp_path):
    initial = Market('btc', ('u', 'd'), 'c', {'markets': [{}]})
    final = Market('btc', ('u', 'd'), 'c', {
        'markets': [{'umaResolutionStatus': 'resolved', 'outcomePrices': '["1","0"]'}]})
    cancelled = []
    async def stream(*args):
        try:
            await asyncio.Future()
        finally:
            cancelled.append(True)
    async def fetch(*args):
        return final
    async def check():
        with patch('btc.lifecycle.record_stream', stream), patch('btc.lifecycle.fetch', fetch):
            await watch(None, initial, tmp_path, poll=.01)
    asyncio.run(check())
    rows = [json.loads(x) for x in (tmp_path/'btc/events.jsonl').read_text().splitlines()]
    assert rows[-2]['kind'] == 'resolution'
    assert rows[-1]['kind'] == 'stop'
    assert cancelled == [True]
