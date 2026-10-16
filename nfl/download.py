import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx

RELEASE_URL = 'https://api.github.com/repos/nflverse/nflverse-data/releases/tags/pbp'


def download(season, output):
    filename = f'play_by_play_{season}.parquet'
    output.mkdir(parents=True,exist_ok=True)
    destination = output/filename
    temporary = output/(filename+'.part')
    with httpx.Client(follow_redirects=True,timeout=60) as client:
        response = client.get(RELEASE_URL)
        response.raise_for_status()
        asset = next((a for a in response.json()['assets'] if a['name']==filename),None)
        if asset is None:
            raise ValueError(f'No play-by-play release for {season}')
        try:
            checksum, size = hashlib.sha256(), 0
            with client.stream('GET',asset['browser_download_url']) as response, temporary.open('wb') as target:
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > min(asset['size'],100_000_000):
                        raise ValueError('Download exceeds expected size or 100 MB limit')
                    checksum.update(chunk)
                    target.write(chunk)
            digest = checksum.hexdigest()
            if size != asset['size'] or (asset.get('digest') and asset['digest'] != 'sha256:'+digest):
                raise ValueError('Release size or checksum mismatch')
            import pyarrow.parquet as parquet
            parquet.ParquetFile(temporary)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    metadata = dict(season=season,asset_id=asset['id'],url=asset['browser_download_url'],
        asset_updated_at=asset['updated_at'],downloaded_at=datetime.now(timezone.utc).isoformat(),
        bytes=size,sha256=digest)
    destination.with_suffix('.source.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(f'Saved {destination} ({size/1e6:.2f} MB)')


def main():
    parser = argparse.ArgumentParser(description='Download official nflverse season play-by-play')
    parser.add_argument('--season',type=int,required=True)
    parser.add_argument('--output',type=Path,default=Path('data/nfl'))
    args = parser.parse_args()
    if not 1999 <= args.season <= 2100:
        parser.error('Season must be between 1999 and 2100')
    download(args.season,args.output)


if __name__ == '__main__':
    main()
