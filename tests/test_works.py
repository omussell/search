from unittest.mock import patch
from unittest import TestCase, main
from flask import request

import requests

from core.service import search_service
from core import constants
from app import app


def mock_works_response(*args, **kwargs):
    return Response(
        json={'status': 'ok', 'message-type': 'work-list', 'message-version': '1.0.0', 'message': {'facets': {}, 'total-results': 22009, 'items': [{'indexed': {'date-parts': [[2022, 4, 1]], 'date-time': '2022-04-01T04:01:54Z', 'timestamp': 1648785714374}, 'reference-count': 0, 'publisher': 'British Editorial Society', 'content-domain': {'domain': [], 'crossmark-restriction': False}, 'published-print': {'date-parts': [[2021, 10, 27]]}, 'DOI': '10.13xx/3114-210xxx', 'type': 'dataset', 'created': {'date-parts': [[2021, 10, 27]], 'date-time': '2021-10-27T13:33:30Z', 'timestamp': 1635341610000}, 'source': 'Crossref', 'is-referenced-by-count': 0, 'title': ["President's Welcome"], 'prefix': '10.1302', 'member': '42', 'container-title': ['OrthoMedia'], 'original-title': ["President's Welcome"], 'deposited': {'date-parts': [[2021, 10, 27]], 'date-time': '2021-10-27T13:33:31Z', 'timestamp': 1635341611000}, 'score': 15.833171, 'resource': {'primary': {'URL': 'https://domain.media/title/876d48a3-c714-4b01-xxx-b6df4dc2xxxx'}}, 'issued': {'date-parts': [[2021, 10, 27]]}, 'references-count': 0, 'URL': 'http://dx.doi.org/10.13xx/3114-210xxx', 'published': {'date-parts': [[2021, 10, 27]]}}, {'indexed': {'date-parts': [[2022, 4, 1]], 'date-time': '2022-04-01T13:32:50Z', 'timestamp': 1648819970528}, 'reference-count': 0, 'publisher': 'Faber and Faber', 'content-domain': {'domain': [], 'crossmark-restriction': False}, 'published-print': {'date-parts': [[2010, 7, 1]]}, 'DOI': '10.50xx/9780571289974.00000xxx', 'type': 'other', 'created': {'date-parts': [[2013, 2, 28]], 'date-time': '2013-02-28T17:48:00Z', 'timestamp': 1362073680000}, 'source': 'Crossref', 'is-referenced-by-count': 4, 'title': ['Welcome to Thebes'], 'prefix': '10.50xx', 'member': '2984', 'container-title': ['Welcome to Thebes'], 'deposited': {'date-parts': [[2020, 5, 21]], 'date-time': '2020-05-21T20:20:09Z', 'timestamp': 1590092409000}, 'score': 15.796868, 'resource': {'primary': {'URL': 'https://www.domain.com/plays/welcome-to-thebes-iid-113xxx'}}, 'issued': {'date-parts': [[2010, 7, 1]]}, 'references-count': 0, 'URL': 'http://dx.doi.org/10.50xx/9780571289974.00000xxx', 'published': {'date-parts': [[2010, 7, 1]]}}], 'items-per-page': 20, 'query': {'start-index': 0, 'search-terms': 'welcome'}}}
    )


def mock_funders_response(*args, **kwargs):
    return mock_works_response(args, kwargs)


def mock_funders_list(*args, **kwargs):
    return Response(
        json={'status': 'ok', 'message-type': 'funder-list', 'message-version': '1.0.0', 'message': {'items-per-page': 20, 'query': {'start-index': 0, 'search-terms': 'na'}, 'total-results': 343, 'items': [{'id': '100005537', 'location': 'United States', 'name': 'National Association of Broadcasters', 'alt-names': ['NAB', 'NABroadcasters', "Nat'l Ass'n of Broadcasters"], 'uri': 'http://dx.doi.org/10.13039/100005537', 'replaces': [], 'replaced-by': [], 'tokens': ['national', 'association', 'of', 'broadcasters', 'nab', 'nabroadcasters', 'natl', 'assn', 'of', 'broadcasters']}, {'id': '100019428', 'location': 'Ireland', 'name': 'Nabriva Therapeutics', 'alt-names': ['Nabriva', 'Nabriva Therapeutics plc'], 'uri': 'http://dx.doi.org/10.13039/100019428', 'replaces': [], 'replaced-by': [], 'tokens': ['nabriva', 'therapeutics', 'nabriva', 'nabriva', 'therapeutics', 'plc']}]}}
    )


class Response:

    def __init__(self, json={}, status_code=200):
        self._json = json
        self.status_code = status_code

    def json(self):
        return self._json


class Request:

    def __init__(self, args_data={}):
        self.args = args_data


class WorksSearch(TestCase):

    def setUp(self) -> None:
        super(WorksSearch, self).setUp()
        self.works_request = Request(args_data={'q': 'welcome'})

    @patch.object(requests, "get", mock_works_response)
    def test_works_search(self):
        with app.test_request_context(path="/search/works?q=welcome"):
            items, page = search_service.search_query(constants.CATEGORY_WORKS, request)
            assert len(items) == 2

            assert "/search/works" in page['sort_url']
            assert page['query'] == 'welcome'
            assert page['total'] == '22009'

    @patch.object(requests, "get", mock_funders_response)
    def test_funders_search(self):
        with app.test_request_context(path="/search/funders?id=100019428"):
            items, page = search_service.search_query(constants.CATEGORY_FUNDERS, request)
            assert len(items) == 2

            assert "/search/funders" in page['sort_url']
            assert page['funder_id'] == '100019428'
            assert page['total'] == '22009'

    @patch.object(requests, "get", mock_funders_list)
    def test_funders_list(self):
        with app.test_request_context(path="/search/funders?q=na"):
            items, page = search_service.search_query(constants.CATEGORY_FUNDERS, request)
            assert len(items) == 2

            assert "/search/funders" in page['sort_url']
            assert "Na" in items[0]['name']
            assert "Na" in items[1]['name']


if __name__ == '__main__':
    main()
