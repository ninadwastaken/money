import asyncio
import json
import ssl
import time
from uuid import uuid4
import certifi
from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException

URL = 'wss://ws-subscriptions-clob.polymarket.com/ws/market'


async def heartbeat(socket):
    while True:
        await socket.send('PING')
        await asyncio.sleep(10)


async def session(market, store):
    context = ssl.create_default_context(cafile=certifi.where())
    async with connect(URL, ssl=context, ping_interval=20, ping_timeout=20,
                       max_queue=1024, max_size=8_000_000) as socket:
        store.write('connection', {'id': uuid4().hex, 'needs_books': market.assets})
        await socket.send(json.dumps(dict(assets_ids=market.assets, type='market',
                                          custom_feature_enabled=True)))
        pending = set(market.assets)
        deadline = time.monotonic() + 15
        ping = asyncio.create_task(heartbeat(socket))
        try:
            while True:
                timeout = min(30, max(.01, deadline-time.monotonic())) if pending else 30
                raw = await asyncio.wait_for(socket.recv(), timeout)
                received = time.time_ns()
                if raw == 'PONG':
                    continue
                store.write('ws', raw, received)
                messages = json.loads(raw)
                for event in messages if isinstance(messages, list) else [messages]:
                    if event.get('event_type') == 'book':
                        pending.discard(event['asset_id'])
                if not pending and deadline is not None:
                    store.write('synced', {'assets': market.assets})
                    deadline = None
                if pending and time.monotonic() >= deadline:
                    raise TimeoutError('Initial books missing')
        finally:
            ping.cancel()
            await asyncio.gather(ping, return_exceptions=True)


async def record_stream(market, store):
    delay = 1
    while True:
        started = time.monotonic()
        try:
            await session(market, store)
        except (OSError, TimeoutError, ValueError, WebSocketException) as error:
            store.write('gap', {'error': str(error), 'resync': 'await fresh WS books'})
        if time.monotonic()-started > 60:
            delay = 1
        await asyncio.sleep(delay)
        delay = min(delay*2, 30)
