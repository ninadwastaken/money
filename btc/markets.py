import json
from dataclasses import dataclass

GAMMA = 'https://gamma-api.polymarket.com'
WINDOW = 900


@dataclass(frozen=True)
class Market:
    slug: str
    assets: tuple[str, ...]
    condition: str
    raw: dict


def slugs(now):
    start = int(now) // WINDOW * WINDOW
    return [f'btc-updown-15m-{start + offset}' for offset in (-900, 0, 900)]


def array(value):
    return json.loads(value) if isinstance(value, str) else value


async def fetch(client, slug):
    response = await client.get(f'{GAMMA}/events/slug/{slug}')
    if response.status_code == 404:
        return None
    response.raise_for_status()
    event = response.json()
    for market in event['markets']:
        if market.get('slug') != slug:
            continue
        outcomes = array(market['outcomes'])
        key = 'positionIds' if market.get('version') == 'v2' else 'clobTokenIds'
        assets = array(market[key])
        if len(assets) != 2 or set(outcomes) != {'Up', 'Down'}:
            raise ValueError(f'Invalid BTC outcomes: {slug}')
        return Market(slug, tuple(assets), market['conditionId'], event)
    raise ValueError(f'Missing market: {slug}')


def resolved(market):
    return any(m.get('umaResolutionStatus') == 'resolved'
               for m in market.raw['markets'])
