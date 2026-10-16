# BTC recorder

```sh
uv sync
uv run btc-record                    # Ctrl+C to stop
uv run btc-record --seconds 60       # Bounded run
uv run pytest
uv run python -m btc.analyze
```

Records BTC 15-minute Polymarket books, trade updates, metadata and resolutions.
Current and next markets are discovered every 10s; metadata refreshes every 30s.
Unresolved recordings resume on restart. No wallet or trading.

`data/<market-slug>/events.jsonl` stores raw messages, receipt timestamps,
run IDs and sequence numbers. Exchange timestamps remain inside raw messages.
`connection`/`gap` invalidate prior books; `synced` follows fresh books for both
outcomes. Each `book` replaces that outcome's book; changes set absolute size
(zero deletes a level). Don't replay changes before that outcome's fresh book.

Reconnects use backoff. Shutdown flushes files. Snapshot streams lack a global
sequence guarantee; silent upstream losses cannot be ruled out. Public trade
updates do not reveal individual queue positions. Reference-price feed is next.

Code: `markets.py` discovery, `stream.py` connection, `storage.py` files,
`lifecycle.py` settlement tracking, `recorder.py` coordination and CLI.

[Stream docs](https://docs.polymarket.com/market-data/realtime-data)

Analysis replays local receipt order, resets books on gaps, and checks ask depth
plus recorded fees. Default: 10 shares/side and 0.5¢ extra cost/pair.
Margins are hypothetical total dollars, not fills or profit. The 3s age filter
uses local book-update receipts; it does not prove low exchange latency.
