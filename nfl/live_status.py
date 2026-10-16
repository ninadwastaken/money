from collections import Counter
import json
import time

from btc.storage import Storage


class LiveStorage(Storage):
    def __init__(self, root, slug):
        super().__init__(root, slug)
        self.slug = slug
        self.counts = Counter()
        self.latest = {}
        self.book_ready = False

    def write(self, kind, payload, received_ns=None):
        received = received_ns or time.time_ns()
        super().write(kind, payload, received)
        self.counts[kind] += 1
        self.latest[kind] = received
        if kind in ('gap', 'connection', 'stop'):
            self.book_ready = False
        elif kind == 'synced':
            self.book_ready = True

    def status(self):
        return dict(slug=self.slug, counts=dict(self.counts), latest_received_ns=self.latest, book_ready=self.book_ready)


def save_status(root, stores, journal):
    temporary = root / 'status.part'
    temporary.write_text(json.dumps(dict(updated_ns=time.time_ns(),
        games={game: store.status() for game, store in stores.items()},
        feed=journal.status()), indent=2) + '\n')
    temporary.replace(root / 'status.json')


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Show NFL recorder health')
    parser.add_argument('folder', type=Path, help='Recording folder for a game date')
    args = parser.parse_args()
    data = json.loads((args.folder / 'status.json').read_text())
    print(f"Status updated {(time.time_ns() - data['updated_ns']) / 1e9:.0f}s ago")
    for game in data['games'].values():
        print(game['slug'], 'books ready:', game['book_ready'], game['counts'])
    print('Sports feed:', data['feed']['counts'])
