import asyncio
import json
from unittest.mock import patch

from nfl.live_sports import session
from nfl.live_status import LiveStorage, save_status


def test_sports_heartbeat_and_game_id_routing_preserve_raw_possession(tmp_path):
    update = dict(gameId=12, leagueAbbreviation='NFL', turn='DAL', period='4Q', elapsed='02:51')
    messages = ['ping', json.dumps(update)]
    sent, finished = [], asyncio.Event()

    class Socket:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def send(self, message):
            sent.append(message)
        async def recv(self):
            if messages:
                return messages.pop(0)
            finished.set()
            await asyncio.Future()

    async def check():
        game = LiveStorage(tmp_path, 'game')
        journal = LiveStorage(tmp_path, 'feed')
        with patch('nfl.live_sports.connect', return_value=Socket()):
            task = asyncio.create_task(session({'12': game}, journal))
            await asyncio.wait_for(finished.wait(), 1)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        game.write('synced', {})
        assert game.book_ready
        game.write('gap', {})
        assert not game.book_ready
        save_status(tmp_path, {'12': game}, journal)
        game.close()
        journal.close()
    asyncio.run(check())
    rows = [json.loads(line) for line in (tmp_path / 'game/events.jsonl').read_text().splitlines()]
    assert sent == ['pong']
    assert rows[0]['payload'] == update
    assert json.loads((tmp_path / 'status.json').read_text())['games']['12']['book_ready'] is False
