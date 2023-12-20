import json

from core.service.orcid_service import create_orcid_claim_json


def test_create_orcid_claim_record(api_response_1, expected_orcid_claim_record_1):
    input = json.loads(api_response_1)
    actual_output = create_orcid_claim_json(input['message'])
    assert json.loads(actual_output) == json.loads(
        expected_orcid_claim_record_1)


def test_create_orcid_claim_record_with_contributor_orcids(api_response_2, expected_orcid_claim_record_2):
    input = json.loads(api_response_2)
    actual_output = create_orcid_claim_json(input['message'])
    assert json.loads(actual_output) == json.loads(
        expected_orcid_claim_record_2)


def test_create_orcid_claim_record_with_isbns(api_response_3, expected_orcid_claim_record_3):
    input = json.loads(api_response_3)
    actual_output = create_orcid_claim_json(input['message'])
    assert json.loads(actual_output) == json.loads(
        expected_orcid_claim_record_3)
