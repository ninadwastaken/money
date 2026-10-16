# Record Sunday moneylines

List games (dates use New York time, including Sunday night games after UTC midnight):
```sh
uv run python -m nfl.recorder --date 2026-10-18 --list
```
Record all listed games; start before 9:30 AM ET on October 18:
```sh
caffeinate -i uv run python -m nfl.recorder --date 2026-10-18
```
Keep the Mac plugged in with the lid open. Ctrl+C stops and flushes files.
No scheduled startup: the command must remain running. Restart appends a new
run to existing files and marks missing history. Only one recorder per folder.

Each game: `data/nfl/live/2026-10-18/<slug>/events.jsonl`.
Saves raw full-depth order books, price changes, trades, game updates, metadata,
and resolution when available. Receipt times use the same local clock.
Connections retry; gaps invalidate prior books until fresh snapshots arrive.
Sports feed fields may be delayed or omit possession; missing `turn` is flagged.
No inferred possession switches, paper fills, or real orders are generated yet.

Check recording health from another terminal:
```sh
uv run python -m nfl.live_status data/nfl/live/2026-10-18
```
Look for recent status, each game's `books ready: True`, increasing `ws` counts,
and sports updates during live games. Review gap and missing-possession counts.
Status refreshes every five seconds between discovery requests.

Optional: `--seconds 60` for a bounded test, or repeat `--slug GAME_SLUG` to
select specific games. Otherwise every listed moneyline is recorded.
