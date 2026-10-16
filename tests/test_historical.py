import pytest
pq = pytest.importorskip('pyarrow.parquet')
import pyarrow as pa
from btc.historical_odds import select
from btc.historical_results import parse
from strategies.models.zero_drift import probability


def test_asof_quotes_exclude_future_and_stale(tmp_path):
    slug = 'btc-updown-15m-1771508700'
    decision = (1771508700+302)*1000
    rows = []
    for side,offset,ask in [('UP',-100,.5),('DOWN',-100,.6),('UP',100,.3),('DOWN',-5000,.2)]:
        rows.append(dict(market_slug=slug,side_label=side,source_ts_ms=decision+offset,
            ingest_ts_ms=decision+offset,best_bid=ask-.01,best_ask=ask))
    path = tmp_path/'quotes.parquet'
    pq.write_table(pa.Table.from_pylist(rows),path)
    selected = select([path])
    assert selected[slug]['up']['best_ask'] == .5
    assert selected[slug]['down']['best_ask'] == .6


def test_official_outcome_mapping_and_rule_window():
    market = dict(slug='btc',umaResolutionStatus='resolved',outcomes='["Down","Up"]',
                  outcomePrices='["1","0"]',description='Uses Chainlink price at beginning and end')
    result = parse({'markets':[market]},'btc')
    assert result['winner'] == 0
    assert result['averaging_seconds'] == 0
    market['description'] = 'https://data.chain.link/btc-usd-twap-60s-streams'
    assert parse({'markets':[market]},'btc')['averaging_seconds'] == 60


def test_point_and_averaged_models_are_distinct():
    assert probability(101,100,600,.001,0) != probability(101,100,600,.001,60)
