from datetime import date, timedelta

REPO = 'gregyoung14/openmarket-btc-polymarket'
REVISION = '74502466d1a7cef56395bfd8d0b465fbebc849cf'
BASE = f'https://huggingface.co/datasets/{REPO}'
TREE = f'https://huggingface.co/api/datasets/{REPO}/tree/{REVISION}/unified/polymarket_ticks_ms'


def inventory(client):
    url, entries = TREE+'?recursive=true&limit=1000', []
    while url:
        response = client.get(url)
        response.raise_for_status()
        entries.extend(response.json())
        url = response.links.get('next',{}).get('url')
    return [r for r in entries if r['type']=='file' and r['path'].endswith('.parquet')]


def plan(client, entries, start, end):
    days = [(start+timedelta(days=i)).isoformat() for i in range((end-start).days+1)]
    available = {day: [r for r in entries if f'/date={day}/' in r['path']] for day in days}
    files, selected = {}, [day for day in days if available[day]]
    for day in selected:
        for index, entry in enumerate(sorted(available[day],key=lambda r:r['path'])):
            name = day+'.parquet' if index==0 else day+'-'+entry['path'].rsplit('/',1)[1]
            files[name] = dict(url=f"{BASE}/resolve/{REVISION}/{entry['path']}",
                bytes=entry['size'], sha256=entry.get('lfs',{}).get('oid'))
    candle_days = sorted({day for day in selected} | {
        (date.fromisoformat(day)-timedelta(days=1)).isoformat() for day in selected})
    for day in candle_days:
        name = f'BTCUSDT-1m-{day}.zip'
        url = f'https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1m/{name}'
        response = client.head(url)
        response.raise_for_status()
        files[name] = dict(url=url,bytes=int(response.headers.get('content-length',0)),sha256=None)
    return files, [day for day in days if not available[day]]
