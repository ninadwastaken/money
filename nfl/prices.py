import json
from datetime import datetime, timezone
from .teams import NAMES
from .possessions import timestamp


def fetch_market(client, plays, folder):
    first = next(p for p in plays if p['time_of_day'])
    day = datetime.fromtimestamp(timestamp(first['time_of_day']),timezone.utc).date().isoformat()
    slug = f"nfl-{first['away_team'].lower()}-{first['home_team'].lower()}-{day}"
    path = folder/(plays[0]['game_id']+'-market.json')
    if path.exists():
        event = json.loads(path.read_text())
    else:
        response = client.get('https://gamma-api.polymarket.com/events/slug/'+slug)
        response.raise_for_status()
        event = response.json()
        path.write_text(json.dumps(event)+'\n')
    expected = {NAMES[first['home_team']],NAMES[first['away_team']]}
    market = next(m for m in event['markets'] if m.get('sportsMarketType')=='moneyline'
                  and set(json.loads(m['outcomes']))==expected)
    return market


def fetch_history(client, token, start, end, path):
    if path.exists():
        return json.loads(path.read_text())
    points, cursor = [], None
    while True:
        params = dict(token_id=token,start=int(start),end=int(end),bucket_seconds=60)
        if cursor:
            params['cursor'] = cursor
        response = client.get('https://data-api.polymarket.com/v2/prices-history',params=params)
        response.raise_for_status()
        payload = response.json()
        points.extend(payload['data'])
        pagination = payload.get('pagination',{})
        next_cursor = pagination.get('next_cursor')
        if not pagination.get('has_more'):
            break
        if not next_cursor or next_cursor==cursor:
            raise ValueError('Invalid history pagination')
        cursor = next_cursor
    path.write_text(json.dumps(points)+'\n')
    return points
