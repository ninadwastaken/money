import asyncio
from datetime import date

import httpx
import pytest

from nfl.live_markets import discover, parse


def event(slug='nfl-dal-gb-2026-10-19'):
    return dict(slug=slug, title='Cowboys vs. Packers', gameId=12,
        teams=[dict(alias='Cowboys'), dict(alias='Packers')], markets=[dict(
            slug=slug, sportsMarketType='moneyline', outcomes='["Cowboys","Packers"]',
            clobTokenIds='["a","b"]', conditionId='condition', gameStartTime='2026-10-19 00:20:00+00')])


def test_discovery_uses_new_york_date_and_ignores_quarter_markets():
    def respond(request):
        payload = [dict(sport='nfl', series='season')] if request.url.path == '/sports' else [
            event(), event('nfl-dal-gb-2026-10-19-highest-scoring-quarter')]
        return httpx.Response(200, json=payload)

    async def check():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            found = await discover(client, date(2026, 10, 18))
            assert len(found) == 1
            assert found[0].game_id == '12'
            assert await discover(client, date(2026, 10, 19)) == []
    asyncio.run(check())


def test_moneyline_validates_teams_and_uses_v2_positions():
    raw = event()
    raw['markets'][0].update(version='v2', positionIds=['p1', 'p2'])
    assert parse(raw).assets == ('p1', 'p2')
    raw['markets'][0]['outcomes'] = '["Yes","No"]'
    with pytest.raises(ValueError, match='outcomes'):
        parse(raw)
