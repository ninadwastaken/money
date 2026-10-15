import asyncio
import httpx
from .markets import fetch, resolved
from .storage import Storage
from .stream import record_stream


async def watch(client, market, root, poll=30):
    store = Storage(root, market.slug)
    stream = None
    try:
        store.write('metadata', market.raw)
        if resolved(market):
            store.write('resolution', market.raw)
            return
        store.write('gap', {'reason': 'startup; earlier history unavailable'})
        stream = asyncio.create_task(record_stream(market, store))
        while True:
            await asyncio.wait({stream}, timeout=poll)
            if stream.done():
                stream.result()
                raise RuntimeError('Stream stopped unexpectedly')
            try:
                latest = await fetch(client, market.slug)
                if latest is None:
                    store.write('metadata_error', {'reason': 'market missing'})
                    continue
                store.write('metadata', latest.raw)
                if resolved(latest):
                    store.write('resolution', latest.raw)
                    return
            except (httpx.HTTPError, ValueError, KeyError) as error:
                store.write('metadata_error', {'error': str(error)})
    finally:
        if stream:
            stream.cancel()
            await asyncio.gather(stream, return_exceptions=True)
        store.write('stop', {'reason': 'watch ended; unresolved unless resolution recorded'})
        store.close()
