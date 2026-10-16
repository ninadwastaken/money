import asyncio
import logging
import time
import httpx
from .lifecycle import watch
from .markets import fetch, slugs


async def discover(client, root, tasks, stop):
    while not stop.is_set():
        for task in tasks.values():
            if task.done():
                task.result()
        pending = {p.name for p in root.glob('btc-updown-15m-*')}
        for slug in sorted(pending | set(slugs(time.time()))):
            if stop.is_set():
                break
            if slug in tasks:
                continue
            try:
                market = await fetch(client,slug)
                if market:
                    tasks[slug] = asyncio.create_task(watch(client,market,root))
                    logging.info('Watching %s',slug)
            except (httpx.HTTPError,ValueError,KeyError) as error:
                logging.warning('%s: %s',slug,error)
        try:
            await asyncio.wait_for(stop.wait(),timeout=10)
        except TimeoutError:
            pass
