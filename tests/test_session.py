from unittest import TestCase, main
from unittest.mock import patch

import requests

from app import app
from core import utils


class Response:

    def __init__(self, json={}, status_code=200) -> None:
        self._json = json
        self.status_code = status_code

    def json(self):
        return self._json


def mock_funders_list(*args, **kwargs):
    return Response(
        json={"token": "11223344", "access_token": "bbbbbb-adad-ccccc-1122aa333bbb4ccc", "token_type": "bearer", "refresh_token": "ea6dcc2b-dfdf-4444-929f-2a6cdb919c35", "expires_in": 631138518, "scope": "/authenticate /activities/update", "name": "John", "orcid": "0000-2222-3333-4444", "expires_at": 2312857989},
    )


class SessionCookieTestCase(TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.secret_key = "your-secret-key"
        self.client = app.test_client()
        utils.set_host_url("http://search.crossref.com/")

    @patch.object(requests, "post", mock_funders_list)
    def test_session_cookie_available(self):
        with self.client as c:
            # Login and set session cookie
            response = c.get("/auth/orcid/callback?code=1234&token=1234")
            assert response.status_code == 200
            signed_in, orcid_info, session_expired = utils.signed_in_info()
            assert signed_in
            assert orcid_info["user_name"] == "John"
            assert orcid_info["access_token"] == "bbbbbb-adad-ccccc-1122aa333bbb4ccc"
            assert orcid_info["orcid"] == "0000-2222-3333-4444"
            assert not session_expired

    def test_session_cookie_not_available(self):
        with self.client as c:
            c.get("/")
            signed_in, orcid_info, session_expired = utils.signed_in_info()
            assert not signed_in
            assert orcid_info is None
            assert not session_expired


if __name__ == "__main__":
    main()
