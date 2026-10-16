import csv
import io
import zipfile


def load(path):
    with zipfile.ZipFile(path) as archive:
        content = archive.read(archive.namelist()[0]).decode()
    rows = []
    for row in csv.reader(io.StringIO(content)):
        start, end = int(row[0]), int(row[6])
        scale = 1_000_000 if start > 10**15 else 1000
        rows.append((start/scale, end/scale, float(row[4]), float(row[1])))
    return sorted(rows)


def history(rows, now, delay=2):
    available = [r for r in rows if r[1]+delay <= now]
    chosen = available[-61:]
    if len(chosen) < 61 or now-chosen[-1][1] > 65:
        return None
    if any(b[0]-a[0] != 60 for a,b in zip(chosen, chosen[1:])):
        return None
    return [r[2] for r in chosen]


def opening_price(rows, start):
    return next((r[3] for r in rows if r[0] == start), None)
