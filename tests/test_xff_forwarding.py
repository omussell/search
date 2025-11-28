from unittest import TestCase, main
from unittest.mock import Mock, patch

import requests
from flask import request

from app import app
from core import constants
from core.service import search_service
from core.service.orcid_service import create_orcid_claim_json
from core.utils import prepare_api_headers


class TestXFFForwarding(TestCase):

    @patch.object(requests, "get")
    def test_xff_forwarded_to_api(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message-type": "work-list", "message": {"total-results": 0, "items": []}}
        mock_get.return_value = mock_response

        with app.test_request_context(path="/search/works?q=test", headers={'X-Forwarded-For': '203.0.113.42'}):
            search_service.search_query(constants.CATEGORY_WORKS, request)
            self.assertEqual(mock_get.call_args.kwargs['headers']['X-Forwarded-For'], '203.0.113.42')

    def test_prepare_api_headers_with_request(self):
        with app.test_request_context(path="/", headers={'X-Forwarded-For': '192.0.2.1'}):
            headers = prepare_api_headers(request)
            self.assertEqual(headers['X-Forwarded-For'], '192.0.2.1')

    def test_prepare_api_headers_without_request(self):
        headers = prepare_api_headers(None)
        self.assertNotIn('X-Forwarded-For', headers)

    def test_prepare_api_headers_with_ip_string(self):
        headers = prepare_api_headers('198.51.100.42')
        self.assertEqual(headers['X-Forwarded-For'], '198.51.100.42')

    @patch.object(requests, "get")
    def test_orcid_path_forwards_xff(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "@article{}"
        mock_get.return_value = mock_response

        create_orcid_claim_json({"DOI": "10.1000/test", "title": ["Test"], "type": "journal-article"}, 
                               client_ip="198.51.100.42")
        
        self.assertEqual(mock_get.call_args.kwargs['headers']['X-Forwarded-For'], "198.51.100.42")


if __name__ == "__main__":
    main()

