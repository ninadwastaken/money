import asyncio

import httpx

from btc.stream import record_stream
from nfl.live_markets import GAMMA


async def watch(client, market, store):
    store.write('metadata', market.raw)
    store.write('gap', {'reason': 'startup; no earlier book history'})
    stream = asyncio.create_task(record_stream(market, store))
    try:
        while True:
            await asyncio.wait({stream}, timeout=30)
            if stream.done():
                stream.result()
                raise RuntimeError('Moneyline stream stopped unexpectedly')
            try:
                response = await client.get(GAMMA + '/events/slug/' + market.slug)
                response.raise_for_status()
                event = response.json()
                store.write('metadata', event)
                selected = next(row for row in event['markets'] if row['conditionId'] == market.condition)
                if selected.get('umaResolutionStatus') == 'resolved':
                    store.write('resolution', event)
                    return
            except (httpx.HTTPError, ValueError, KeyError, StopIteration) as error:
                store.write('metadata_error', {'error': str(error)})
    finally:
        stream.cancel()
        await asyncio.gather(stream, return_exceptions=True)
        store.write('stop', {'reason': 'market watch ended'})
