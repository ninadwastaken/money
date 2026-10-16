import asyncio
from datetime import date
import json
from types import SimpleNamespace

from nfl import live_runtime


def test_shutdown_cancels_all_feeds_and_flushes_stores(monkeypatch, tmp_path):
    cancelled = []

    async def discover(*args):
        return [SimpleNamespace(slug='game', game_id='12', assets=('a','b'),
                    starts=date(2026,10,18), title='Game')]

    async def sports(*args):
        try:
            await asyncio.Future()
        finally:
            cancelled.append('sports')

    async def watch(client, market, store):
        try:
            store.write('synced', {})
            await asyncio.Future()
        finally:
            store.write('stop', {})
            cancelled.append('market')

    async def check():
        stop = asyncio.Event()
        asyncio.get_running_loop().call_later(.02, stop.set)
        await live_runtime.capture(None, tmp_path, date(2026,10,18), set(), stop)

    monkeypatch.setattr(live_runtime, 'discover', discover)
    monkeypatch.setattr(live_runtime, 'record', sports)
    monkeypatch.setattr(live_runtime, 'watch', watch)
    asyncio.run(check())
    assert set(cancelled) == {'sports','market'}
    status = json.loads((tmp_path / 'status.json').read_text())
    assert status['games']['12']['counts']['stop'] == 1
    assert status['feed']['counts']['stop'] == 1
