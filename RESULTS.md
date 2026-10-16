# Research results

Updated 2026-10-16. All money figures below are hypothetical, not real trades.
Append each new run with its rule, sample, costs, result, limitations, and report.
Keep losing runs and earlier samples; overlapping samples must not be added together.
Reports under `data/` are saved locally and ignored by Git; this log is tracked.

Frozen for future paper testing on 2026-10-16: [NFL defense rule](strategies/nfl_defense_frozen.txt).
Buy defense +30s, sell on return to offense; no new buys at 2:30 or less in
regulation or during overtime. Live recording is built; paper-fill simulation
and verification of possession fields during an NFL game are still pending.

## Historical data audit (2026-10-16)

Downloaded all API pages for all 80 saved 2026 NFL moneyline markets, including
maker records and trades as small as 0.000001 shares, into `data/nfl/trades-all/`.
571,474 participant records (386,773 during game windows), versus 211,120
original taker records. All original records found in expanded history;
zero additional active seconds. Extra participant records are not new distinct
fills; do not feed maker sides directly into the existing taker-price screen.
Each game has a pagination/filter manifest. This confirms API exhaustion, not
independent on-chain completeness or historical order-book coverage.

Bills–Rams cross-check: separate legacy endpoint returned exactly the same
6,148 taker records across seven pages, including with the smaller size filter.
Both endpoints belong to Polymarket; this is not an independent source.
Public PMXT order-book probes: 2026-09-13T20 and 2026-10-11T17 UTC files returned
404; control 2026-09-09T16 returned 200. Those probes do not establish absence
of all historical NFL order books from every provider. Quotes remain unverified.
Reports: [expanded history](data/nfl/history-audit/expanded-comparison.json),
[legacy comparison](data/nfl/history-audit/legacy-comparison.json),
[download coverage](data/nfl/trades-all/coverage.json).

## NFL: buy defense, sell on return to offense

Rule: buy the defending team 30 seconds after defense starts; sell when that same
team returns to offense. If it never returns before game end, hold to settlement.
Both switches use recorded drive starts/first offensive plays, not verified
possession-acquisition times. This can include time after commercial breaks.

80 games, 1,714 candidate entries; $10 per entry including estimated buy fees.
Use same-token BUY fills for entry and SELL fills for exit, at most 5 seconds old.
Same-second fills use volume-weighted prices; terminal exits use official payouts.

| Outcome | Entries | Hypothetical profit after estimated fees |
|---|---:|---:|
| Returned to offense; sold | 31 | +$71.02 |
| Game ended first; settled | 8 | -$35.66 |
| Combined | 39 | +$35.35 |

27/39 positive across 31 games. Missing recent trades: 1,650 candidates;
possession ended before entry: 25. Only 2.3% of candidates were screened.
Completed fills do not prove executable prices or available size. No execution
delay/slippage modeled; fees use current cached metadata. Missing-data selection
and approximate switch times can materially change results. No held-out test.
Status: worth investigating; no established trading edge.
Report: [defense return](data/nfl/defense-return/screen.json).

Five-minute cutoff variant: same rule, but no new buys at 5:00 or less remaining
in regulation; no overtime buys. Existing positions retain all outcomes.
80 games; 21 usable entries across 19 games; 15 positive; hypothetical +$20.81
after estimated fees on $10 entries. No usable positions reached settlement.
220 candidates excluded by cutoff/unknown clock, 1,472 missing prices, 1 ended
before entry. Cutoff uses the latest prior play clock minus elapsed wall time,
conservatively assuming the game clock kept running; it can exclude extra buys
near 5:00. Same price/timing limits; variant chosen after viewing original results.
Report: [five-minute cutoff](data/nfl/defense-return/screen-cutoff-300s.json).

Three-minute cutoff variant: no new buys at 3:00 or less remaining in regulation;
no overtime buys. Same entry, exit, fees, and conservative clock method as above.
80 games; 23 usable entries across 20 games; 16 positive; hypothetical +$23.16
on $10 entries after estimated fees. No usable positions reached settlement.
159 candidates excluded by cutoff/unknown clock, 1,530 missing prices, 2 ended
before entry. Same sample reused to compare cutoffs; not independent validation.
Report: [three-minute cutoff](data/nfl/defense-return/screen-cutoff-180s.json).

Additional cutoffs, same 80 games and assumptions; $10 entries after estimated fees:

| Stop buying at | Usable entries | Games with entries | Positive | Hypothetical profit |
|---|---:|---:|---:|---:|
| 2:30 remaining | 24 | 21 | 17 | +$26.36 |
| 2:00 remaining | 25 | 21 | 17 | +$23.08 |

Neither run had usable settlement entries. At 2:30: 137 cutoff/unknown-clock
exclusions, 1,551 missing-price pairs, 2 possessions ended before entry.
At 2:00: 119 exclusions, 1,568 missing-price pairs, 2 ended before entry.
These are comparisons on the same sample, not independent evidence of an edge.
Reports: [2:30](data/nfl/defense-return/screen-cutoff-150s.json),
[2:00](data/nfl/defense-return/screen-cutoff-120s.json).

Broader-window variant (separate from frozen exact-time rule): first same-team
BUY fill 20-40s after defense starts; first SELL fill 0-20s after return to offense.
Chronological first fill, not best price. Apply 2:30 cutoff at selected entry time;
no overtime buys. Same $10 sizing, estimated fees, and timing/price caveats.
80 games; 109 usable entries across 47 games; 63 positive; hypothetical -$19.66.
One usable position settled. Missing entry-window trade: 914; missing exit-window
trade: 604; cutoff/unknown clock: 67; possession ended before entry: 20.
Statuses are checked in sequence and are not directly comparable to earlier
cutoff counts. Missing exits leave outcomes unmeasured, not zero-profit trades.
This larger filtered sample reverses the earlier positive result; no validated edge.
Report: [broader windows](data/nfl/defense-return/bands-cutoff-150s.json).

## NFL: fixed-time exits (different rules)

Entry/exit seconds below are both measured from the defense-start proxy.
Each total assumes $10 per entry and estimated fees. Trades must be no older
than the age limit. Same pricing/timing limitations as above.

| Games searched | Price age limit | Buy → sell | Usable entries | Hypothetical profit |
|---:|---:|---|---:|---:|
| 15 | 2s | 10s → 30s | 7 | -$5.20 |
| 15 | 2s | 10s → 60s | 1 | -$5.82 |
| 15 | 2s | 30s → 90s | 2 | +$1.09 |
| 15 | 5s | 10s → 30s | 14 | -$13.74 |
| 15 | 5s | 10s → 60s | 4 | -$8.56 |
| 15 | 5s | 30s → 90s | 8 | +$3.90 |
| 15 | 10s | 10s → 30s | 25 | -$12.98 |
| 15 | 10s | 10s → 60s | 19 | -$12.74 |
| 15 | 10s | 30s → 90s | 18 | +$2.47 |
| 80 | 5s | 10s → 30s | 28 | -$16.62 |
| 80 | 5s | 10s → 60s | 18 | -$21.18 |
| 80 | 5s | 30s → 90s | 29 | -$1.85 |

The original 8-entry positive result disappeared in the expanded sample.
Reports: [2s](data/nfl/fixed-timing/trade-screen-2s.json),
[5s](data/nfl/fixed-timing/trade-screen-5s.json),
[10s](data/nfl/fixed-timing/trade-screen-10s.json),
[80 games](data/nfl/fixed-timing/season-trade-screen-5s.json).

Earlier chart screen: buy defense +60s, exit on possession end/settlement.
15 games, 321 entries; average -3.57 cents/share before fees, -4.59 cents/share
after estimated fees. Minute prices; 128 approximate exits. Not executable P&L.
Report: [chart screen](data/nfl/defense-screen/screen.json).

## BTC: probability model versus market odds

Paired recording audit (2026-10-16): Coinbase contains 60 minutes, 29,883 new
trade messages, two connections and two initial book snapshots. Four BTC rounds
have fresh two-outcome Polymarket books at the fixed open+302s decision time
during Coinbase coverage. All four officially resolved Down; the final label
was fetched after recording stopped. This sample cannot train and independently
test an Up/Down logistic model. Thousands of ticks do not add independent round
labels. No logistic model trained or profitability calculated from this hour.
Reports: [decision audit](data/paired-decision-audit.json),
[recording inventory](data/paired-data-audit.json),
[recovered official outcome](data/paired-outcomes.json).

Zero-drift model using Binance minute returns and EWMA volatility; decide 302s
after market open, trade if estimated edge exceeds 2 percentage points.
Illustrative fees and same-snapshot fills; price proxy, depth, latency, and
historical fees remain unverified. Dollar sizing differs from the NFL tests.

| Sample | Hypothetical trades | Hypothetical profit |
|---|---:|---:|
| Local recording pilot | 1 | -$2.29 |
| February–March archive | 17 | -$21.61 |
| May archive | 23 | +$2.69 |
| Combined February–March + May | 40 | -$18.92 |

Combined: 79 rounds. Model probability error (Brier) 0.21135 versus market
0.20405; lower is better. No demonstrated improvement over market odds.
Reports: [pilot](data/baseline-comparison.json),
[February–March](data/history/comparison-feb-mar.json),
[May](data/history/may-comparison.json),
[combined](data/history/comparison-combined.json).
`comparison.json` duplicates the February–March result; do not double count it.

Earlier live-book check found no immediate profitable purchase of both BTC
outcomes after costs in the observed recording. No standalone result report
was located for that run; this is a qualitative historical note.
