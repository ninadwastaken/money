import json
import time
from uuid import uuid4


class Storage:
    def __init__(self, root, slug):
        folder = root / slug
        folder.mkdir(parents=True, exist_ok=True)
        self.file = (folder / 'events.jsonl').open('a', buffering=1)
        self.run = uuid4().hex
        self.sequence = 0

    def write(self, kind, payload, received_ns=None):
        self.sequence += 1
        record = dict(version=1, run=self.run, sequence=self.sequence,
                      received_ns=received_ns or time.time_ns(),
                      monotonic_ns=time.monotonic_ns(), kind=kind, payload=payload)
        self.file.write(json.dumps(record, separators=(',', ':')) + '\n')

    def close(self):
        self.file.close()
