import argparse
import asyncio
import logging
import signal
import ssl
from pathlib import Path
import certifi
import httpx
from .discovery import discover
from .coinbase import record as record_coinbase


async def run(root, seconds=None):
    stop, tasks = asyncio.Event(), {}
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    timer = loop.call_later(seconds, stop.set) if seconds else None
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        async with httpx.AsyncClient(timeout=10, verify=context) as client:
            tasks['coinbase'] = asyncio.create_task(record_coinbase(root))
            try:
                await discover(client,root,tasks,stop)
            finally:
                for task in tasks.values():
                    task.cancel()
                await asyncio.gather(*tasks.values(),return_exceptions=True)
    finally:
        if timer:
            timer.cancel()
        for task in tasks.values():
            task.cancel()
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logging.error('Market task failed: %s', result)
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(sig)


def main():
    parser = argparse.ArgumentParser(description='Record BTC 15-minute public markets')
    parser.add_argument('--output', type=Path, default=Path('data'))
    parser.add_argument('--seconds', type=float, help='Stop after this many seconds')
    args = parser.parse_args()
    if args.seconds is not None and args.seconds <= 0:
        parser.error('--seconds must be positive')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    asyncio.run(run(args.output, args.seconds))


if __name__ == '__main__':
    main()
