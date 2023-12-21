import json
import os
from core.service.orcid_service import create_orcid_claim_json


def load_test_data(filename, test_data_dir):
    file_path = os.path.join(test_data_dir, filename)
    with open(file_path, 'r') as file:
        return json.load(file)


def update_test_data(api_response_file, output_file, test_data_dir):
    api_response = load_test_data(api_response_file, test_data_dir)
    updated_output = create_orcid_claim_json(api_response['message'])
    output_path = os.path.join(test_data_dir, output_file)
    with open(output_path, 'w') as file:
        json.dump(json.loads(updated_output), file, indent=4)


def main():
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    tests = [
        ('works_api_response_1.json', 'orcid_claim_1.json'),
        ('works_api_response_2.json', 'orcid_claim_2.json'),
        ('works_api_response_3.json', 'orcid_claim_3.json'),
    ]

    for api_response_file, output_file in tests:
        update_test_data(api_response_file, output_file, test_data_dir)
        print(f"Updated {output_file} based on {api_response_file}")


if __name__ == "__main__":
    main()
