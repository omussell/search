import json
from unittest.mock import patch

from core.service.orcid_service import create_orcid_claim_json


def test_create_orcid_claim_record(api_response_1, expected_orcid_claim_record_1):
    input = json.loads(api_response_1)
    expected = json.loads(expected_orcid_claim_record_1)
    mock_bibtex = expected.get('citation', {}).get('citation-value', '')
    
    with patch('core.service.orcid_service.fetch_citation_bibtex', return_value=mock_bibtex):
        actual_output = create_orcid_claim_json(input['message'])
        assert json.loads(actual_output) == expected


def test_create_orcid_claim_record_with_contributor_orcids(api_response_2, expected_orcid_claim_record_2):
    input = json.loads(api_response_2)
    expected = json.loads(expected_orcid_claim_record_2)
    mock_bibtex = expected.get('citation', {}).get('citation-value', '')
    
    with patch('core.service.orcid_service.fetch_citation_bibtex', return_value=mock_bibtex):
        actual_output = create_orcid_claim_json(input['message'])
        assert json.loads(actual_output) == expected


def test_create_orcid_claim_record_with_isbns(api_response_3, expected_orcid_claim_record_3):
    input = json.loads(api_response_3)
    expected = json.loads(expected_orcid_claim_record_3)
    mock_bibtex = expected.get('citation', {}).get('citation-value', '')
    
    with patch('core.service.orcid_service.fetch_citation_bibtex', return_value=mock_bibtex):
        actual_output = create_orcid_claim_json(input['message'])
        assert json.loads(actual_output) == expected
