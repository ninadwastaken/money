import hashlib
from datetime import date
import httpx
import pytest
from btc.archive import download
from btc.archive_catalog import inventory, plan
from btc.archive_files import transfer


def test_plan_skips_missing_days_and_adds_warmup():
    entry = dict(type='file',path='unified/polymarket_ticks_ms/date=2026-05-14/part-000001.parquet',size=10)
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,headers={'content-length':'20'}))) as client:
        files,missing = plan(client,[entry],date(2026,5,13),date(2026,5,15))
    assert missing == ['2026-05-13','2026-05-15']
    assert set(files) == {'2026-05-14.parquet','BTCUSDT-1m-2026-05-13.zip','BTCUSDT-1m-2026-05-14.zip'}


def test_inventory_follows_pagination():
    def reply(request):
        if 'page=2' in str(request.url):
            return httpx.Response(200,json=[dict(type='file',path='b.parquet',size=2)])
        return httpx.Response(200,json=[dict(type='file',path='a.parquet',size=1)],
            headers={'link':'<https://huggingface.co/page=2>; rel="next"'})
    with httpx.Client(transport=httpx.MockTransport(reply)) as client:
        assert len(inventory(client)) == 2


def test_cache_verified_and_manifest_preserved(tmp_path):
    entry = dict(url='https://example.org/file',bytes=3,sha256=hashlib.sha256(b'abc').hexdigest())
    calls = []
    def reply(request):
        calls.append(1)
        return httpx.Response(200,content=b'abc')
    with httpx.Client(transport=httpx.MockTransport(reply)) as client:
        download(client,{'first':entry},tmp_path,10)
        download(client,{'first':entry},tmp_path,10)
        download(client,{'second':entry},tmp_path,10)
    import json
    assert len(calls) == 2
    assert set(json.loads((tmp_path/'sources.json').read_text())['files']) == {'first','second'}


def test_budget_and_dry_run_do_not_create_files(tmp_path):
    root = tmp_path/'absent'
    files = {'a':dict(url='https://example.org/a',bytes=100,sha256=None)}
    with httpx.Client() as client:
        with pytest.raises(ValueError):
            download(client,files,root,10)
        download(client,files,root,100,dry_run=True)
    assert not root.exists()


def test_failed_transfer_keeps_original_and_removes_partial(tmp_path):
    path = tmp_path/'a'
    path.write_bytes(b'original')
    entry = dict(url='https://example.org/a',bytes=3,sha256=None)
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b'ab'))) as client:
        with pytest.raises(ValueError):
            transfer(client,path,entry,100)
    assert path.read_bytes() == b'original'
    assert not (tmp_path/'a.part').exists()
