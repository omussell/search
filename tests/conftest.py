import pytest
from utils import load_test_data

# Expected ORCID claim JSON output


@pytest.fixture
def expected_orcid_claim_record_1():
    data = load_test_data('orcid_claim_1.json')
    return data


@pytest.fixture
def expected_orcid_claim_record_2():
    data = load_test_data('orcid_claim_2.json')
    return data


@pytest.fixture
def expected_orcid_claim_record_3():
    data = load_test_data('orcid_claim_3.json')
    return data

# Expected Crossref Works API JSON output


@pytest.fixture
def api_response_1():
    data = load_test_data('works_api_response_1.json')
    return data


@pytest.fixture
def api_response_2():
    return load_test_data('works_api_response_2.json')


@pytest.fixture
def api_response_3():
    return load_test_data('works_api_response_3.json')


@pytest.fixture  # Work with institutional author
def api_response_4():
    return load_test_data('works_api_response_4.json')
