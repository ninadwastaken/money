import hashlib
import json


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def cached(path, entry, previous):
    if not path.exists() or (entry['bytes'] and path.stat().st_size != entry['bytes']):
        return False
    expected = entry.get('sha256') or previous.get('sha256')
    if previous.get('url') != entry['url'] and not entry.get('sha256'):
        return False
    return bool(expected) and digest(path)==expected


def transfer(client, path, entry, limit):
    temporary = path.with_name(path.name+'.part')
    try:
        with client.stream('GET',entry['url']) as response, temporary.open('wb') as out:
            response.raise_for_status()
            size = 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > limit:
                    raise ValueError(f'{path.name} exceeds download budget')
                out.write(chunk)
        if entry['bytes'] and size != entry['bytes']:
            raise ValueError(f'{path.name}: incomplete download')
        actual = digest(temporary)
        if entry.get('sha256') and entry['sha256'] != actual:
            raise ValueError(f'{path.name}: checksum mismatch')
        temporary.replace(path)
        return size
    finally:
        temporary.unlink(missing_ok=True)


def save_manifest(path, manifest):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(manifest,indent=2)+'\n')
    temporary.replace(path)
