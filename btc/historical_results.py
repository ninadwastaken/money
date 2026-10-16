"""Cache official historical outcomes/rules separately from model inputs."""
import asyncio
import json
from pathlib import Path
import httpx
from .markets import array

ROOT = Path('data/history')


def parse(event, slug):
    market = next(m for m in event['markets'] if m['slug'] == slug)
    if market.get('umaResolutionStatus') != 'resolved':
        raise ValueError('No official resolved outcome')
    outcomes, prices = array(market['outcomes']), list(map(float,array(market['outcomePrices'])))
    if sorted(prices) != [0,1] or set(outcomes) != {'Up','Down'}:
        raise ValueError('Unexpected outcome encoding')
    rules = market['description']
    if 'twap-60s' in rules.lower():
        window = 60
    elif 'chainlink' in rules.lower() and 'twap' not in rules.lower():
        window = 0
    else:
        raise ValueError('Unrecognized settlement rule')
    return dict(winner=int(prices[outcomes.index('Up')]), averaging_seconds=window,
                official_target=event.get('eventMetadata',{}).get('priceToBeat'), rules=rules)


async def download():
    slugs = sorted(json.loads((ROOT/'quotes.json').read_text()))
    folder = ROOT/'official'
    folder.mkdir(exist_ok=True)
    semaphore = asyncio.Semaphore(5)
    async with httpx.AsyncClient(timeout=20) as client:
        async def one(slug):
            path = folder/(slug+'.json')
            async with semaphore:
                if path.exists():
                    return
                try:
                    response = await client.get('https://gamma-api.polymarket.com/events/slug/'+slug)
                    response.raise_for_status()
                    event = response.json()
                    parse(event,slug)
                    path.write_text(json.dumps(event)+'\n')
                except (httpx.HTTPError,ValueError,KeyError,StopIteration) as error:
                    print(slug,str(error),flush=True)
        await asyncio.gather(*(one(slug) for slug in slugs))
    print('Official outcomes cached:',len(list(folder.glob('*.json'))),flush=True)


if __name__ == '__main__':
    asyncio.run(download())
