"""One as-of quote per outcome, five minutes after each historical market opens."""
import math
import pyarrow.parquet as pq
import pyarrow.compute as pc


def select(paths, max_age=3):
    markets = {}
    columns = ['market_slug','side_label','source_ts_ms','ingest_ts_ms','best_bid','best_ask']
    for path in paths:
        for batch in pq.ParquetFile(path).iter_batches(columns=columns):
            batch = batch.filter(pc.match_substring_regex(batch.column(0),r'^btc-updown-15m-[0-9]{10}$'))
            starts = pc.cast(pc.utf8_slice_codeunits(batch.column(0), start=-10), 'int64')
            decisions = pc.add(pc.multiply(starts,1000),302000)
            age = pc.subtract(decisions,batch.column(3))
            mask = pc.and_(pc.greater_equal(age,0),pc.less_equal(age,max_age*1000))
            for row in batch.filter(mask).to_pylist():
                slug = row['market_slug']
                if not slug.startswith('btc-updown-15m-'):
                    continue
                start = int(slug.rsplit('-',1)[1])
                decision = (start+302)*1000
                if not decision-max_age*1000 <= row['ingest_ts_ms'] <= decision:
                    continue
                if not decision-max_age*1000 <= row['source_ts_ms'] <= decision:
                    continue
                bid, ask = row['best_bid'], row['best_ask']
                if bid is None or ask is None or not all(math.isfinite(x) for x in (bid,ask)):
                    continue
                if not 0 < bid < ask < 1:
                    continue
                side = row['side_label'].lower()
                if side not in ('up','down'):
                    continue
                previous = markets.setdefault(slug,{}).get(side)
                if previous is None or row['ingest_ts_ms'] > previous['ingest_ts_ms']:
                    markets[slug][side] = row
    return {slug: quotes for slug,quotes in markets.items() if len(quotes)==2}
