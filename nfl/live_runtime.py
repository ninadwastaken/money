import asyncio
import logging
import time

import httpx

from nfl.live_markets import discover
from nfl.live_sports import record
from nfl.live_status import LiveStorage, save_status
from nfl.live_watch import watch


async def capture(client, root, day, slugs, stop):
    stores, jobs = {}, {}
    journal = LiveStorage(root, '_feed')
    sports = asyncio.create_task(record(stores, journal))
    refresh = 0
    try:
        while not stop.is_set():
            if sports.done():
                sports.result()
                raise RuntimeError('Sports recorder stopped unexpectedly')
            if time.monotonic() >= refresh:
                try:
                    markets = await discover(client, day)
                    for market in markets:
                        if (slugs and market.slug not in slugs) or market.slug in jobs:
                            continue
                        store = LiveStorage(root, market.slug)
                        stores[market.game_id] = store
                        jobs[market.slug] = asyncio.create_task(watch(client, market, store))
                        journal.write('selected_market', dict(slug=market.slug, game_id=market.game_id,
                            assets=market.assets, kickoff=market.starts.isoformat()))
                        logging.info('Recording %s', market.title)
                    journal.write('discovery', dict(found=len(markets), recording=len(jobs)))
                except (httpx.HTTPError, ValueError, KeyError, StopIteration) as error:
                    journal.write('discovery_error', {'error': str(error)})
                    logging.error('Discovery: %s', error)
                refresh = time.monotonic() + 60
            for task in jobs.values():
                if task.done():
                    task.result()
            save_status(root, stores, journal)
            try:
                await asyncio.wait_for(stop.wait(), 5)
            except TimeoutError:
                pass
    finally:
        tasks = [sports, *jobs.values()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        journal.write('stop', {'reason': 'recorder stopped'})
        save_status(root, stores, journal)
        for store in [journal, *stores.values()]:
            store.close()
