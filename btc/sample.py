"""Download and inspect only OpenMarket's small demo tables."""
import hashlib
import json
from pathlib import Path
import httpx
import pyarrow.parquet as pq

from .archive_catalog import REPO, REVISION
TABLES = ('market_meta', 'binance_ticks_ms', 'polymarket_ticks_ms', 'lag_pairs_ms')
ROOT = Path('data/openmarket-sample')


def download():
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest = {'repository': REPO, 'revision': REVISION, 'files': {}}
    with httpx.Client(follow_redirects=True, timeout=60) as client:
        for name in TABLES:
            filename = name + '.parquet'
            url = f'https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{filename}'
            with client.stream('GET', url) as response:
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > 5_000_000:
                        raise ValueError('Sample exceeded 5 MB limit')
                    chunks.append(chunk)
            content = b''.join(chunks)
            (ROOT/filename).write_bytes(content)
            manifest['files'][filename] = dict(bytes=size, sha256=hashlib.sha256(content).hexdigest())
    (ROOT/'source.json').write_text(json.dumps(manifest, indent=2)+'\n')


def inspect():
    report, market_sets = {}, {}
    for name in TABLES:
        table = pq.read_table(ROOT/(name+'.parquet'))
        rows = table.to_pylist()
        key = 'market_slug'
        market_sets[name] = {r[key] for r in rows if r.get(key)}
        report[name] = dict(rows=len(rows), markets=len(market_sets[name]),
            schema={f.name: str(f.type) for f in table.schema},
            nulls={c: table[c].null_count for c in table.column_names})
        if 'source_ts_ms' in table.column_names and rows:
            times = [r['source_ts_ms'] for r in rows if r['source_ts_ms'] is not None]
            report[name]['source_range_ms'] = [min(times), max(times)] if times else []
        if name == 'market_meta':
            report[name]['resolved_labels'] = sum(bool(r.get('resolved_outcome')) for r in rows)
        print(name, json.dumps(report[name]))
    report['metadata_tick_markets'] = sorted(market_sets['market_meta'] & market_sets['polymarket_ticks_ms'])
    (ROOT/'inspection.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Metadata-matched Polymarket markets:', len(report['metadata_tick_markets']))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true')
    if parser.parse_args().download:
        download()
    inspect()
