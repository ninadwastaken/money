import asyncio
import json
from pathlib import Path
from unittest.mock import patch
import httpx
from btc.markets import fetch, slugs, resolved, Market
from btc.storage import Storage
from btc.stream import session, record_stream


def test_rollover():
    assert slugs(1791936899)[1] == 'btc-updown-15m-1791936000'
    assert slugs(1791936900)[0] == 'btc-updown-15m-1791936000'
    assert slugs(1791936900)[1] == 'btc-updown-15m-1791936900'


def test_mapping_and_rules():
    market = dict(slug='btc', conditionId='c', outcomes='["Down","Up"]',
                  clobTokenIds='["d","u"]', description='TWAP', feeSchedule={'rate': .07})
    async def check():
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json={'markets': [market]}))
        async with httpx.AsyncClient(transport=transport) as client:
            result = await fetch(client, 'btc')
            assert result.assets == ('d', 'u')
            assert result.raw['markets'][0]['description'] == 'TWAP'
            assert not resolved(result)
    asyncio.run(check())


def test_storage_append_and_timestamps(tmp_path):
    for _ in range(2):
        store = Storage(tmp_path, 'btc')
        store.write('ws', '{"timestamp":"123"}', 456)
        store.close()
    rows = [json.loads(x) for x in (tmp_path/'btc/events.jsonl').read_text().splitlines()]
    assert rows[0]['payload'] == '{"timestamp":"123"}'
    assert rows[0]['received_ns'] == 456
    assert rows[0]['run'] != rows[1]['run']


def test_reconnect_marks_gap_and_cancellation(tmp_path):
    market = Market('btc', ('u', 'd'), 'c', {})
    calls = []
    async def broken(*args):
        calls.append(1)
        raise OSError('disconnected')
    async def check():
        store = Storage(tmp_path, 'btc')
        with patch('btc.stream.session', broken):
            task = asyncio.create_task(record_stream(market, store))
            await asyncio.sleep(1.05)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        store.close()
    asyncio.run(check())
    assert len(calls) == 2
    rows = (tmp_path/'btc/events.jsonl').read_text().splitlines()
    assert all(json.loads(x)['kind'] == 'gap' for x in rows)
