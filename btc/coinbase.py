"""Public BTC-USD books and trades; Coinbase is a signal feed, not settlement."""
import asyncio
import json
import logging
import ssl
import time
from uuid import uuid4
import certifi
from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException
from .coinbase_quality import Quality
from .storage import Storage

URL = 'wss://ws-feed.exchange.coinbase.com'
CHANNELS = ['level2_batch','matches','heartbeat']


async def session(store):
    context = ssl.create_default_context(cafile=certifi.where())
    async with connect(URL,ssl=context,ping_interval=20,ping_timeout=20,
                       max_queue=1024,max_size=16_000_000) as socket:
        store.write('connection',dict(id=uuid4().hex,url=URL,product='BTC-USD',channels=CHANNELS))
        await socket.send(json.dumps(dict(type='subscribe',product_ids=['BTC-USD'],channels=CHANNELS)))
        quality, deadline = Quality(), time.monotonic()+15
        while True:
            timeout = 10 if quality.ready else max(.01,min(10,deadline-time.monotonic()))
            raw = await asyncio.wait_for(socket.recv(),timeout)
            received = time.time_ns()
            store.write('ws',raw,received)
            event = json.loads(raw)
            if event.get('product_id','BTC-USD') != 'BTC-USD':
                continue
            marker = quality.observe(event)
            if marker:
                store.write(*marker,received_ns=received)
                if marker[0] == 'synced':
                    logging.info('Coinbase BTC-USD book synchronized')
            if not quality.ready and time.monotonic() >= deadline:
                raise TimeoutError('Coinbase initial snapshot missing')


async def record(root):
    store = Storage(root,'coinbase-btc-usd')
    delay = 1
    try:
        store.write('gap',{'reason':'startup; previous feed history unavailable'})
        store.write('metadata',dict(venue='Coinbase Exchange',product='BTC-USD',
            channels=CHANNELS,book_batch_ms=50,trade_side='maker; aggressor is opposite',
            last_match='historical reference, not a new trade',settlement_feed=False))
        while True:
            started = time.monotonic()
            try:
                await session(store)
            except (OSError,TimeoutError,ValueError,WebSocketException) as error:
                store.write('gap',{'error':str(error),'resync':'fresh book snapshot on reconnect'})
                logging.warning('Coinbase reconnect: %s',error)
            if time.monotonic()-started > 60:
                delay = 1
            await asyncio.sleep(delay)
            delay = min(delay*2,30)
    finally:
        store.write('stop',{'reason':'recorder stopped'})
        store.close()
