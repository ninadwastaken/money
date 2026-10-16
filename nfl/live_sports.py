import asyncio
import json
import ssl
import time

import certifi
from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException

URL = 'wss://sports-api.polymarket.com/ws'


def route(raw, stores, received):
    messages = json.loads(raw)
    for event in messages if isinstance(messages, list) else [messages]:
        if not isinstance(event, dict) or event.get('leagueAbbreviation', '').lower() != 'nfl':
            continue
        store = stores.get(str(event.get('gameId')))
        if store:
            store.write('sports', event, received)
            if event.get('live') and not event.get('turn'):
                store.write('possession_missing', {'game_id': event['gameId']}, received)


async def session(stores, journal):
    context = ssl.create_default_context(cafile=certifi.where())
    async with connect(URL, ssl=context, ping_interval=20, ping_timeout=20, max_size=8_000_000) as socket:
        journal.write('sports_connection', {'needs_fresh_state': True})
        while True:
            raw = await asyncio.wait_for(socket.recv(), timeout=20)
            received = time.time_ns()
            if raw == 'ping':
                await socket.send('pong')
                journal.write('sports_heartbeat', {}, received)
                continue
            journal.write('sports_raw', raw, received)
            route(raw, stores, received)


async def record(stores, journal):
    delay = 1
    while True:
        started = time.monotonic()
        try:
            await session(stores, journal)
        except (OSError, TimeoutError, ValueError, WebSocketException) as error:
            journal.write('sports_gap', {'error': str(error), 'possession_state_invalid': True})
            for store in stores.values():
                store.write('sports_gap', {'error': str(error)})
        delay = 1 if time.monotonic() - started > 60 else min(delay * 2, 30)
        await asyncio.sleep(delay)
