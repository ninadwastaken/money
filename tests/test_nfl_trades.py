import json

import httpx
import pytest

from nfl.trades import download


def test_download_follows_cursor_and_reuses_complete_cache(tmp_path):
    calls = []

    def respond(request):
        calls.append(request.url.params.get('cursor'))
        more = len(calls) == 1
        return httpx.Response(200, json=dict(data=[dict(timestamp=len(calls))],
            pagination=dict(has_more=more, next_cursor='next' if more else None)))

    path = tmp_path / 'trades.json'
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        rows = download(client, 'condition', path)
        assert download(client, 'condition', path) == rows
    assert calls == [None, 'next']
    assert json.loads(path.read_text()) == [dict(timestamp=1), dict(timestamp=2)]


def test_failed_page_does_not_cache_partial_history(tmp_path):
    def respond(request):
        if request.url.params.get('cursor'):
            return httpx.Response(503)
        return httpx.Response(200, json=dict(data=[dict(timestamp=1)],
            pagination=dict(has_more=True, next_cursor='next')))

    path = tmp_path / 'trades.json'
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            download(client, 'condition', path)
    assert not path.exists()


def test_download_records_filters_and_rejects_incompatible_cache(tmp_path):
    def respond(request):
        assert request.url.params['taker_only'] == 'false'
        assert float(request.url.params['filter_amount']) == .000001
        return httpx.Response(200, json=dict(data=[], pagination=dict(has_more=False)))

    path = tmp_path / 'trades.json'
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        assert download(client, 'condition', path, include_makers=True, minimum_size=.000001) == []
        with pytest.raises(ValueError, match='different filters'):
            download(client, 'condition', path)
    manifest = json.loads(path.with_suffix('.manifest.json').read_text())
    assert manifest['complete_api_pagination']
    assert manifest['pages'][0]['rows'] == 0
