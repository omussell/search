import json
import pytest
from unittest.mock import patch, MagicMock

import requests
from core import exceptions
from core.service.orcid_service import add_contributors, add_external_ids, add_pub_date, add_titles, create_orcid_claim_json, extract_orcid_dois, orcid_work_type

from core.service.orcid_service import pad_date_item, to_issn, to_isbn, extract_doi, fetch_citation_bibtex


@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock_get:
        yield mock_get


# Create a fixture that patches 'core.utils.CONFIG' globally
@pytest.fixture(autouse=True)
def mock_config():
    with patch('core.utils.CONFIG', {'ORCID_MEMBER_URL': 'https://api.orcid.org/v2.0/'}):
        yield


@pytest.mark.parametrize("input,expected_output", [
    (1, "01"),
    (11, "11"),
    ("5", "05"),
    (None, None),
    ("invalid", None),
    (-1, None)
])
def test_pad_date_item(input, expected_output):
    assert pad_date_item(input) == expected_output


@pytest.mark.parametrize("input_uri, expected_output", [
    ("http://id.crossref.org/issn/1234-5678", "1234-5678"),
    ("http://id.crossref.org/issn/8765-4321", "8765-4321"),
    ("http://invalid.uri/issn/0000-0000", None),
    ("Not a URI", None),
    (12345, None)
])
def test_to_issn(input_uri, expected_output):
    assert to_issn(input_uri) == expected_output


@pytest.mark.parametrize("input_uri, expected_output", [
    ("http://id.crossref.org/isbn/978-3-16-148410-0", "978-3-16-148410-0"),
    ("http://id.crossref.org/isbn/978-1-23-456789-7", "978-1-23-456789-7"),
    ("http://invalid.uri/isbn/000-0-00-000000-0", None),
    ("Just a string", None),
    (12345, None)
])
def test_to_isbn(input_uri, expected_output):
    assert to_isbn(input_uri) == expected_output


@pytest.mark.parametrize("input_record, expected_output", [
    ({"DOI": "10.1000/xyz123"}, "10.1000/xyz123"),
    # Testing with leading/trailing spaces
    ({"DOI": " 10.1000/xyz123 "}, "10.1000/xyz123"),
    ({"DOI": 12345}, None),  # Non-string DOI
    ({"NoDOI": "10.1000/xyz123"}, None),  # Missing DOI key
    ("NotADict", None),  # Invalid type for work_record
])
def test_extract_doi(input_record, expected_output):
    assert extract_doi(input_record) == expected_output


@pytest.fixture
def mock_requests_post():
    with patch('requests.post') as mock_post:
        yield mock_post


def test_add_external_ids_with_doi():
    record = {}
    doi_record = {"DOI": "10.1000/xyz123", "url": "http://example.com"}
    add_external_ids(record, doi_record)
    assert record["external-ids"]["external-id"][0]["external-id-type"] == "doi"
    assert record["external-ids"]["external-id"][0]["external-id-value"] == "10.1000/xyz123"


def test_add_external_ids_without_doi():
    record = {}
    doi_record = {}
    add_external_ids(record, doi_record)
    # Ensure external-ids is not in record or its external-id list is empty
    assert "external-ids" not in record or not record["external-ids"]["external-id"]


def test_add_external_ids_with_issn():
    record = {}
    doi_record = {
        "issn-type": [{"value": "1234-5678", "type": "electronic"}]
    }
    add_external_ids(record, doi_record)
    assert record["external-ids"]["external-id"][0]["external-id-type"] == "issn"
    assert record["external-ids"]["external-id"][0]["external-id-value"] == "1234-5678"


def test_add_external_ids_without_issn():
    record = {}
    doi_record = {}
    add_external_ids(record, doi_record)
    # Ensure no ISSN is present in the external-ids
    assert "external-ids" not in record or not any(
        ext_id["external-id-type"] == "issn" for ext_id in record["external-ids"].get("external-id", []))


def test_add_external_ids_with_isbn():
    record = {}
    doi_record = {
        "isbn-type": [{"value": "978-3-16-148410-0", "type": "print"}]
    }
    add_external_ids(record, doi_record)
    assert record["external-ids"]["external-id"][0]["external-id-type"] == "isbn"
    assert record["external-ids"]["external-id"][0]["external-id-value"] == "978-3-16-148410-0"


def test_add_external_ids_without_isbn():
    record = {}
    doi_record = {}
    add_external_ids(record, doi_record)
    # Ensure no ISBN is present in the external-ids
    assert "external-ids" not in record or not any(
        ext_id["external-id-type"] == "isbn" for ext_id in record["external-ids"].get("external-id", []))


def test_add_external_ids_with_doi_issn_isbn():
    record = {}
    doi_record = {
        "DOI": "10.1000/xyz123",
        "issn-type": [{"value": "1234-5678", "type": "electronic"}],
        "isbn-type": [{"value": "978-3-16-148410-0", "type": "print"}]
    }
    add_external_ids(record, doi_record)
    assert any(ext_id["external-id-type"] ==
               "doi" for ext_id in record["external-ids"]["external-id"])
    assert any(ext_id["external-id-type"] ==
               "issn" for ext_id in record["external-ids"]["external-id"])
    assert any(ext_id["external-id-type"] ==
               "isbn" for ext_id in record["external-ids"]["external-id"])


def test_add_external_ids_issn_prefer_electronic():
    record = {}
    doi_record = {
        "issn-type": [
            {"value": "1234-5678", "type": "print"},
            {"value": "8765-4321", "type": "electronic"}
        ]
    }
    add_external_ids(record, doi_record)
    assert record["external-ids"]["external-id"][0]["external-id-type"] == "issn"
    # Electronic preferred
    assert record["external-ids"]["external-id"][0]["external-id-value"] == "8765-4321"


def test_add_external_ids_issn_only_print():
    record = {}
    doi_record = {
        "issn-type": [{"value": "1234-5678", "type": "print"}]
    }
    add_external_ids(record, doi_record)
    assert record["external-ids"]["external-id"][0]["external-id-type"] == "issn"
    assert record["external-ids"]["external-id"][0]["external-id-value"] == "1234-5678"


def test_add_external_ids_isbn_prefer_electronic():
    record = {}
    doi_record = {
        "isbn-type": [
            {"value": "978-3-16-148410-0", "type": "print"},
            {"value": "978-1-23-456789-7", "type": "electronic"}
        ]
    }
    add_external_ids(record, doi_record)
    assert record["external-ids"]["external-id"][0]["external-id-type"] == "isbn"
    # Electronic preferred
    assert record["external-ids"]["external-id"][0]["external-id-value"] == "978-1-23-456789-7"


def test_add_external_ids_isbn_only_print():
    record = {}
    doi_record = {
        "isbn-type": [{"value": "978-3-16-148410-0", "type": "print"}]
    }
    add_external_ids(record, doi_record)
    assert record["external-ids"]["external-id"][0]["external-id-type"] == "isbn"
    assert record["external-ids"]["external-id"][0]["external-id-value"] == "978-3-16-148410-0"


def test_add_titles_with_title():
    record = {}
    doi_record = {"title": "Sample Title"}
    add_titles(record, doi_record)
    assert record["title"]["title"]["value"] == "Sample Title"


def test_add_titles_without_title():
    record = {}
    doi_record = {}
    add_titles(record, doi_record)
    assert "title" not in record


def test_add_titles_with_subtitle():
    record = {}
    doi_record = {"title": "Sample Title", "subtitle": "Sample Subtitle"}
    add_titles(record, doi_record)
    assert record["title"]["subtitle"]["value"] == "Sample Subtitle"


def test_add_titles_without_subtitle():
    record = {}
    doi_record = {"title": "Sample Title"}
    add_titles(record, doi_record)
    assert "subtitle" not in record["title"]


def test_add_titles_with_container_title():
    record = {}
    doi_record = {"title": "Sample Title", "container-title": "Sample Journal"}
    add_titles(record, doi_record)
    assert record["journal-title"]["value"] == "Sample Journal"


def test_add_titles_without_container_title():
    record = {}
    doi_record = {"title": "Sample Title"}
    add_titles(record, doi_record)
    assert "journal-title" not in record


def test_add_titles_with_all_elements():
    record = {}
    doi_record = {
        "title": "Sample Title",
        "subtitle": "Sample Subtitle",
        "container-title": "Sample Journal"
    }
    add_titles(record, doi_record)
    assert record["title"]["title"]["value"] == "Sample Title"
    assert record["title"]["subtitle"]["value"] == "Sample Subtitle"
    assert record["journal-title"]["value"] == "Sample Journal"


def test_add_contributors_with_author_and_editor():
    record = {}
    doi_record = {
        "author": [{"given": "John", "family": "Doe"}],
        "editor": [{"given": "Jane", "family": "Smith"}]
    }
    add_contributors(record, doi_record)
    assert len(record["contributors"]["contributor"]) == 2
    assert record["contributors"]["contributor"][0]["credit-name"]["value"] == "Doe, John"
    assert record["contributors"]["contributor"][0]["contributor-attributes"]["contributor-role"] == "author"
    assert record["contributors"]["contributor"][1]["credit-name"]["value"] == "Smith, Jane"
    assert record["contributors"]["contributor"][1]["contributor-attributes"]["contributor-role"] == "editor"


def test_add_contributors_with_only_author():
    record = {}
    doi_record = {"author": [{"given": "John", "family": "Doe"}]}
    add_contributors(record, doi_record)
    assert len(record["contributors"]["contributor"]) == 1
    assert record["contributors"]["contributor"][0]["credit-name"]["value"] == "Doe, John"
    assert record["contributors"]["contributor"][0]["contributor-attributes"]["contributor-role"] == "author"


def test_add_contributors_with_only_editor():
    record = {}
    doi_record = {"editor": [{"given": "Jane", "family": "Smith"}]}
    add_contributors(record, doi_record)
    assert len(record["contributors"]["contributor"]) == 1
    assert record["contributors"]["contributor"][0]["credit-name"]["value"] == "Smith, Jane"
    assert record["contributors"]["contributor"][0]["contributor-attributes"]["contributor-role"] == "editor"


def test_add_contributors_with_missing_information():
    record = {}
    doi_record = {}  # No contributor information
    add_contributors(record, doi_record)

    # Assert that the 'contributors' key should not exist in the record
    assert "contributors" not in record


def test_add_contributors_with_partial_information():
    record = {}
    doi_record = {"author": [{"given": "John"}]}  # Missing family name
    add_contributors(record, doi_record)
    assert len(record["contributors"]["contributor"]) == 1
    assert record["contributors"]["contributor"][0]["credit-name"]["value"] == "John"


@pytest.mark.parametrize("doi_record, expected_contributors", [
    (
        {
            "author": [
                {
                    "given": "John",
                    "family": "Doe",
                    "ORCID": "http://orcid.org/0000-0002-1014-621X"
                },
                {
                    "given": "Jane",
                    "family": "Smith"
                }
            ]
        },
        [
            {
                "credit-name": {"value": "Doe, John"},
                "contributor-attributes": {"contributor-role": "author"},
                "contributor-orcid": {
                    "uri": "https://orcid.org/0000-0002-1014-621X",
                    "path": "0000-0002-1014-621X",
                    "host": "orcid.org"
                }
            },
            {
                "credit-name": {"value": "Smith, Jane"},
                "contributor-attributes": {"contributor-role": "author"}
            }
        ]
    ),
])
def test_add_contributors(doi_record, expected_contributors):
    record = {}
    add_contributors(record, doi_record)
    assert "contributors" in record
    assert record["contributors"]["contributor"] == expected_contributors


def test_extract_orcid_dois_success(mock_requests_get):

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "group": [{
            "external-ids": {
                "external-id": [{
                    "external-id-type": "doi",
                    "external-id-value": "10.1000/xyz123"
                }]
            }
        }]
    }
    mock_requests_get.return_value = mock_response
    account_info = {"access_token": "token123",
                    "orcid": "0000-0000-0000-0000"}

    dois = extract_orcid_dois(account_info)
    assert dois == ["10.1000/xyz123"]


def test_extract_orcid_dois_api_failure(mock_requests_get):
    mock_requests_get.side_effect = requests.RequestException(
        "API request failed")
    account_info = {"access_token": "token123", "orcid": "0000-0000-0000-0000"}

    with pytest.raises(exceptions.APIConnectionException):
        extract_orcid_dois(account_info)


def test_extract_orcid_dois_empty_doi_list(mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"group": []}  # No DOI data
    mock_requests_get.return_value = mock_response
    account_info = {"access_token": "token123", "orcid": "0000-0000-0000-0000"}

    dois = extract_orcid_dois(account_info)
    assert dois == []


def test_extract_orcid_dois_malformed_data(mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulating malformed DOI data with an incorrect string
    mock_response.json.return_value = {
        "group": [{
            "external-ids": {
                "external-id": [{
                    "external-id-type": "doi",
                    "external-id-value": None
                }]
            }
        }]
    }
    mock_requests_get.return_value = mock_response
    account_info = {"access_token": "token123", "orcid": "0000-0000-0000-0000"}

    dois = extract_orcid_dois(account_info)
    assert dois == []


def test_extract_orcid_dois_non_200_response(mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_requests_get.return_value = mock_response
    account_info = {"access_token": "token123", "orcid": "0000-0000-0000-0000"}

    with patch('logging.error') as mock_logging_error:
        extract_orcid_dois(account_info)
        expected_error_message = "API returns error. Status Code: 404 - Message: Not Found"
        mock_logging_error.assert_called_with(expected_error_message)


def test_extract_orcid_dois_authentication_issue(mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_requests_get.return_value = mock_response
    account_info = {"access_token": "expired_token",
                    "orcid": "0000-0000-0000-0000"}

    with patch('logging.error') as mock_logging_error:
        extract_orcid_dois(account_info)
        expected_error_message = "API returns error. Status Code: 401 - Message: Unauthorized"
        mock_logging_error.assert_called_with(expected_error_message)


def test_create_orcid_claim_json_with_citation():
    mock_doi_record = {'DOI': '10.1000/xyz123',
                       'title': 'Sample Title', 'type': 'journal-article'}
    mock_citation_bibtex = "@article{sample, title={Sample Title}}"

    with patch('core.service.orcid_service.fetch_citation_bibtex', return_value=mock_citation_bibtex):
        orcid_json = json.loads(create_orcid_claim_json(mock_doi_record))

        assert 'citation' in orcid_json
        assert orcid_json['citation']['citation-type'] == 'bibtex'
        assert orcid_json['citation']['citation-value'] == mock_citation_bibtex


@pytest.mark.parametrize("print_date, online_date, expected_year, expected_month, expected_day", [
    # Test cases with only print date
    ([2014, 8, 5], None, '2014', '08', '05'),
    ([2014], None, '2014', None, None),
    ([1784, 11, 12], None, '1784', '11', '12'),
    ([None, 11, 12], None, None, None, None),
    ([], None, None, None, None),
    # Test cases with only online date
    (None, [2015, 10, 4], '2015', '10', '04'),
    (None, [2015], '2015', None, None),
    # Test cases with both print and online dates
    ([2014, 8, 5], [2013, 7, 4], '2013', '07', '04'),
    ([2016, 1, 1], [2016, 2, 2], '2016', '01', '01'),
    ([2017], [2016], '2016', None, None)
])
def test_add_pub_date(print_date, online_date, expected_year, expected_month, expected_day):
    record = {}
    doi_record = {
        'DOI': '10.1000/xyz123', 'title': 'Sample Article Title', 'type': 'journal-article'
    }
    if print_date is not None:
        doi_record["published-print"] = {"date-parts": [print_date]}
    if online_date is not None:
        doi_record["published-online"] = {"date-parts": [online_date]}

    record = add_pub_date(record, doi_record)

    if expected_year is None:
        assert 'publication-date' not in record
    else:
        assert record['publication-date']['year']['value'] == expected_year
        if expected_month is not None:
            assert record['publication-date']['month']['value'] == expected_month
        else:
            assert 'month' not in record['publication-date']
        if expected_day is not None:
            assert record['publication-date']['day']['value'] == expected_day
        else:
            assert 'day' not in record['publication-date']


@pytest.mark.parametrize("internal_type, expected_orcid_type", [
    ('journal-article', 'journal-article'),
    ('conference-paper', 'conference-paper'),
    ('dissertation', 'dissertation'),
    ('report', 'report'),
    ('standards-and-policy', 'standards-and-policy'),
    ('data-set', 'data-set'),
    ('book', 'book'),
    ('journal', 'journal-issue'),
    ('unknown-type', 'other'),  # Testing the default case
])
def test_orcid_work_type(internal_type, expected_orcid_type):
    assert orcid_work_type(internal_type) == expected_orcid_type
