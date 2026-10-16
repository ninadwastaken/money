from dataclasses import dataclass
from datetime import datetime
import re
from zoneinfo import ZoneInfo

from btc.markets import array

GAMMA = 'https://gamma-api.polymarket.com'


@dataclass(frozen=True)
class GameMarket:
    slug: str
    assets: tuple[str, ...]
    condition: str
    game_id: str
    starts: datetime
    title: str
    raw: dict


def parse(event):
    expected = {team['alias'] for team in event.get('teams', [])}
    for market in event['markets']:
        if market.get('sportsMarketType') != 'moneyline' or market['slug'] != event['slug']:
            continue
        outcomes = array(market['outcomes'])
        assets = array(market['positionIds'] if market.get('version') == 'v2' else market['clobTokenIds'])
        if len(assets) != 2 or len(set(assets)) != 2 or set(outcomes) != expected:
            raise ValueError(f"Unexpected moneyline outcomes: {event['slug']}")
        return GameMarket(event['slug'], tuple(assets), market['conditionId'], str(event['gameId']),
            datetime.fromisoformat(market['gameStartTime'].replace('Z', '+00:00')), event['title'], event)
    raise ValueError(f"No full-game moneyline: {event['slug']}")


async def discover(client, day):
    response = await client.get(GAMMA + '/sports')
    response.raise_for_status()
    sport = next(row for row in response.json() if row['sport'] == 'nfl')
    found = []
    for offset in range(0, 10000, 100):
        response = await client.get(GAMMA + '/events', params=dict(
            series_id=sport['series'], closed='false', limit=100, offset=offset))
        response.raise_for_status()
        events = response.json()
        for event in events:
            if not re.fullmatch(r'nfl-[a-z]+-[a-z]+-\d{4}-\d{2}-\d{2}', event['slug']) or not event.get('gameId'):
                continue
            market = parse(event)
            if market.starts.astimezone(ZoneInfo('America/New_York')).date() == day:
                found.append(market)
        if len(events) < 100:
            return sorted({game.slug: game for game in found}.values(), key=lambda game: game.starts)
    raise ValueError('NFL discovery exceeded pagination limit')
