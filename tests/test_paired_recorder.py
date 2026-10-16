import asyncio
from unittest.mock import patch
from btc.recorder import run


def test_both_feeds_run_and_stop_together(tmp_path):
    started, stopped = [], []
    async def feed(root):
        started.append('coinbase')
        try:
            await asyncio.Future()
        finally:
            stopped.append('coinbase')
    async def discover(client,root,tasks,stop):
        await asyncio.sleep(0)
        started.append('polymarket')
        assert 'coinbase' in started
        stop.set()
    async def check():
        with patch('btc.recorder.record_coinbase',feed),patch('btc.recorder.discover',discover):
            await run(tmp_path,seconds=1)
    asyncio.run(check())
    assert started == ['coinbase','polymarket']
    assert stopped == ['coinbase']
