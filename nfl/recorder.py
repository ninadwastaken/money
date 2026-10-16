import argparse
import asyncio
from datetime import date, datetime, timedelta
import fcntl
import logging
from pathlib import Path
import signal
import ssl
from zoneinfo import ZoneInfo

import certifi
import httpx

from nfl.live_markets import discover
from nfl.live_runtime import capture


async def run(args):
    context = ssl.create_default_context(cafile=certifi.where())
    async with httpx.AsyncClient(timeout=15, verify=context) as client:
        if args.list:
            for game in await discover(client, args.date):
                print(game.starts.astimezone(ZoneInfo('America/New_York')).strftime('%I:%M %p ET'),
                      game.title, game.slug)
            return
        root = args.output / args.date.isoformat()
        root.mkdir(parents=True, exist_ok=True)
        with (root / '.recorder.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            stop, loop = asyncio.Event(), asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, stop.set)
            timer = loop.call_later(args.seconds, stop.set) if args.seconds else None
            try:
                await capture(client, root, args.date, set(args.slug), stop)
            finally:
                if timer:
                    timer.cancel()
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.remove_signal_handler(sig)


def main():
    today = datetime.now(ZoneInfo('America/New_York')).date()
    sunday = today + timedelta(days=(6 - today.weekday()) % 7)
    parser = argparse.ArgumentParser(description='Record NFL full-game moneylines and game updates')
    parser.add_argument('--date', type=date.fromisoformat, default=sunday, help='Game date in New York')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--slug', action='append', default=[], help='Only record this game; repeat to select several')
    parser.add_argument('--output', type=Path, default=Path('data/nfl/live'))
    parser.add_argument('--seconds', type=float, help='Stop after a bounded test run')
    args = parser.parse_args()
    if args.seconds is not None and args.seconds <= 0:
        parser.error('--seconds must be positive')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    asyncio.run(run(args))


if __name__ == '__main__':
    main()
