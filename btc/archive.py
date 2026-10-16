"""Download available historical odds and matching BTC candles by date range."""
import argparse
import json
from datetime import date
from pathlib import Path
import httpx
from .archive_catalog import REVISION, inventory, plan
from .archive_files import cached, digest, save_manifest, transfer

ROOT = Path('data/history')


def download(client, files, root, budget, dry_run=False):
    source = root/'sources.json'
    manifest = json.loads(source.read_text()) if source.exists() else dict(revision=REVISION,files={})
    if manifest['revision'] != REVISION:
        raise ValueError('Output contains a different dataset revision')
    pending = [name for name,entry in files.items()
               if not cached(root/name,entry,manifest['files'].get(name,{}))]
    expected = sum(files[name]['bytes'] for name in pending)
    unknown = sum(not files[name]['bytes'] for name in pending)
    print(f'{len(files)} files; {len(pending)} to download; {expected/1e6:.2f} MB known size; {unknown} unknown sizes')
    if expected > budget:
        raise ValueError('Download exceeds --max-mb; narrow the dates or increase the limit')
    if dry_run:
        return
    root.mkdir(parents=True,exist_ok=True)
    spent = 0
    for name,entry in files.items():
        if name in pending:
            spent += transfer(client,root/name,entry,budget-spent)
        path = root/name
        manifest['files'][name] = dict(url=entry['url'],bytes=path.stat().st_size,sha256=digest(path))
        save_manifest(source,manifest)
        print(('Downloaded ' if name in pending else 'Cached ')+name,flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',type=date.fromisoformat)
    parser.add_argument('--end',type=date.fromisoformat)
    parser.add_argument('--list',action='store_true',help='List available archive dates')
    parser.add_argument('--dry-run',action='store_true',help='Check availability and size without saving files')
    parser.add_argument('--max-mb',type=int,default=500,help='Total new download budget, decimal MB')
    parser.add_argument('--output',type=Path,default=ROOT)
    args = parser.parse_args()
    if not args.list and (not args.start or not args.end or args.end < args.start):
        parser.error('Provide --start and --end in YYYY-MM-DD order')
    if args.max_mb <= 0:
        parser.error('--max-mb must be positive')
    try:
        with httpx.Client(follow_redirects=True,timeout=60) as client:
            entries = inventory(client)
            if args.list:
                print('\n'.join(sorted({r['path'].split('date=')[1].split('/')[0] for r in entries})))
                return
            files, missing = plan(client,entries,args.start,args.end)
            if missing:
                print('No odds archive for: '+', '.join(missing))
            if not files:
                raise ValueError('No available odds dates in requested range')
            download(client,files,args.output,args.max_mb*1_000_000,args.dry_run)
    except (httpx.HTTPError,ValueError) as error:
        parser.exit(1,str(error)+'\n')


if __name__ == '__main__':
    main()
