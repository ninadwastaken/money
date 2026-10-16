# BTC recorder

Research history: [results](RESULTS.md). Future ideas: [strategies](strategies/ideas.txt).
Live NFL moneylines: [recording instructions](docs/nfl-recording.md).

```sh
uv sync
uv run btc-record                    # Ctrl+C to stop
uv run btc-record --seconds 60       # Bounded run
uv run pytest
uv run python -m btc.analyze
```

Records BTC 15-minute Polymarket markets plus Coinbase BTC-USD books/trades.
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

Baseline comparison (requires matching Binance minute-candle ZIP):
```sh
uv run python -m btc.compare data/btc-prices/BTCUSDT-1m-2026-10-15.zip
```
One prediction at five minutes per market; completed candles only. Uses a
Binance return proxy, not the settlement feed. Official winners score results.
Output: `data/baseline-comparison.json`. Trade results assume same-snapshot fills.

Historical downloads:
```sh
uv run python -m btc.archive --list
uv run python -m btc.archive --start 2026-02-16 --end 2026-03-05 --dry-run
uv run python -m btc.archive --start 2026-02-16 --end 2026-03-05
```
Dates are inclusive. Missing archive dates are listed and skipped. Matching BTC
candles and prior-day warmup are included. Files save to `data/history/`;
verified downloads are reused. Default new-download limit: 500 MB (`--max-mb`).
Historical scores: `data/history/comparison.json`; quote-only trade estimates
use standardized fees and assume fills.

The same `btc-record` command now records both feeds. Coinbase raw data saves
to `data/coinbase-btc-usd/events.jsonl` with matching local receipt timestamps.
Its public book feed batches updates every 50 ms; it is not the settlement feed.
Trade `side` means maker side (aggressor is opposite); `last_match` is historical.
`trade_gap` flags incomplete trade history; no backfill is attempted. Reconnects
require a new snapshot. Exclude affected windows when building features.
[Coinbase feed](https://docs.cdp.coinbase.com/exchange/websocket-feed/channels)

NFL play-by-play and historical moneyline trades:
```sh
uv run --extra research python -m nfl.download --season 2026
uv run --extra research python -m nfl.trades
```
Discovers markets for all saved season games and reuses completed downloads.
Use `--since YYYY-MM-DD` to limit games or `--plays PATH` for another season.
Trades: `data/nfl/trades/`; missing games and counts: `coverage.json` there.
Broader raw history, including maker records and tiny fills:
```sh
uv run --extra research python -m nfl.trades --include-makers --minimum-size 0.000001 --output data/nfl/trades-all
uv run python -m nfl.audit_history
```
Maker rows can describe the same fills as taker rows; do not count them as
additional independent trades or feed them directly into the taker-price screen.
