import json
import logging
import requests
from core import exceptions
from core.utils import DOIRecordParser, get_app_config
from datetime import datetime


def orcid_work_type(internal_work_type):
    """Map internal work type to ORCID work type."""
    mapping = {
        'journal-article': 'journal-article',
        'conference-paper': 'conference-paper',
        'dissertation': 'dissertation',
        'report': 'report',
        'standards-and-policy': 'standards-and-policy',
        'data-set': 'data-set',
        'book': 'book',
        'journal': 'journal-issue'
    }
    return mapping.get(internal_work_type, 'other')


def extract_date(doi_record, pub_type):
    """Extracts year, month, and day from the works api DOI record.

    Args:
        doi_record (dict): A dictionary containing works api DOI record data.
        pub_type (str): A string indicating the type of publication.

    Returns:
        tuple: A triple of (year, month, day). Each can be an int or None.

    The function handles different scenarios for the date-parts format:
        - Empty list: Returns (None, None, None) if the date-parts list is empty.
        - List with only year: If the list contains only the year, month and day are set to None.
        - List with year and month: If the list contains year and month, day is set to None.
        - List with year, month, and day: Extracts all three components if available.
        - Non-list format: Treats it as just a year, with month and day as None.
    """

    # Check if the publication type and date-parts are in the DOI record
    if pub_type in doi_record and 'date-parts' in doi_record[pub_type]:
        date_parts = doi_record[pub_type]['date-parts'][0]

        # Process the date-parts if it's a list
        if isinstance(date_parts, list):
            # Check for an empty list
            if not date_parts:
                return None, None, None

            # Extend the list with None to ensure it has at least three elements,
            # then slice the first three to get year, month, and day
            year, month, day = (date_parts + [None, None])[:3]
            return year, month, day
        else:
            # If date_parts is not a list, assume it's just the year
            year, month, day = date_parts, None, None
            return year, month, day

    # Return None for each component if pub_type or date-parts are not found
    return None, None, None


def create_date(y, m, d):
    """Create a date object for comparison, defaulting month and day to January 1st if not provided."""
    return datetime(y, m or 1, d or 1)


def add_pub_date(record, doi_record):
    """
    Adds the earliest publication date (print or online) to the ORCID claim record.

    Args:
        record (dict): The ORCID claim record to which the publication date will be added.
        doi_record (dict): The DOI record containing publication date information.

    The function processes the following use cases:
        - Prioritizes online publication dates over print ones.
        - Extracts date information for 'published-online' and 'published-print'.
        - Determines the earliest date between the two.
        - Formats and adds the earliest date to the ORCID claim record.

    Returns:
        dict: The updated ORCID claim record with the earliest publication date added.
    """

    # Initialize variables to store the earliest date and its components
    earliest_date = None
    year, month, day = None, None, None

    # Iterate over publication types, preferring online over print
    for pub_type in ['published-online', 'published-print']:
        # Extract the date from the DOI record for the current publication type
        y, m, d = extract_date(doi_record, pub_type)

        # Proceed if a valid year is found
        if y is not None:
            # Create a date object
            date = create_date(y, m, d)

            # Update earliest_date if this is the first found date or if it's earlier than the current earliest
            if earliest_date is None or date < earliest_date:
                earliest_date = date
                year, month, day = y, m, d

    # Add the publication date to the record if a valid date was found
    if year is not None:
        # Initialize the publication_date dictionary with the year
        publication_date = {'year': {"value": str(year)}}

        # Add month and day to the publication_date if available
        if month is not None:
            publication_date['month'] = {"value": pad_date_item(month)}
        if day is not None:
            publication_date['day'] = {"value": pad_date_item(day)}

        # Add the publication_date dictionary to the record
        record['publication-date'] = publication_date

    # Return the updated record
    return record


def fetch_citation_bibtex(doi):
    # Fetch citation data in BibTeX format
    response = requests.get(f"https://api.crossref.org/v1/works/{doi}/transform?mailto={get_app_config('API_MAILTO')}",
                            headers={'Accept': 'application/x-bibtex'})
    if response.status_code == 200:
        return response.text
    return None


def extract_doi(work_record):
    """
    Extracts the DOI from a given work record.

    :param work_record: A dictionary containing work record information.
    :return: The extracted DOI as a string or None if the DOI is not found or the input is invalid.
    """
    if not isinstance(work_record, dict) or 'DOI' not in work_record:
        return None

    doi = work_record.get('DOI')
    if not isinstance(doi, str):
        return None

    return doi.strip()


def to_isbn(uri):
    """
    Extracts the ISBN from a given URI.

    :param uri: A string URI that contains the ISBN.
    :return: The extracted ISBN as a string or None if the ISBN is not found.
    """
    if not isinstance(uri, str):
        return None

    prefix = "http://id.crossref.org/isbn/"
    if uri.startswith(prefix):
        return uri[len(prefix):]
    return None


def to_issn(uri):
    """
    Extracts the ISSN from a given URI.

    :param uri: A string URI that contains the ISSN.
    :return: The extracted ISSN as a string or None if the ISSN is not found.
    """
    if not isinstance(uri, str):
        return None

    prefix = "http://id.crossref.org/issn/"
    if uri.startswith(prefix):
        return uri[len(prefix):]
    return None


def pad_date_item(item):
    """
    Pads a date item (month or day) with a leading zero if it's a single digit.
    Returns None for invalid inputs or out-of-range values.

    :param item: The item to pad (expected to be a month or day number).
    :return: A string of the padded item or None.
    """
    try:
        item_int = int(str(item).strip())
        if 0 <= item_int <= 31:  # Assume the range for days
            return f"{item_int:02d}"
    except ValueError:
        pass
    return None


def add_external_ids(record, doi_record):
    """
    Adds external identifiers like DOI, ISBN, and ISSN to an ORCID claim record.

    Args:
        record (dict): The ORCID claim record to which external IDs will be added.
        doi_record (dict): The DOI record containing external ID information.

    The function processes the following use cases:
        - Adds a DOI identifier if present in the DOI record.
        - Adds ISBN and ISSN identifiers, preferring electronic over print versions.
        - Logs a warning if the DOI is missing.
    """

    # List to hold valid external IDs
    external_ids = []

    # Add DOI to the record if present
    if "DOI" in doi_record and doi_record["DOI"]:
        # Append DOI information to the external-id list
        external_ids.append({
            "external-id-type": "doi",
            "external-id-value": doi_record["DOI"],
            "external-id-url": {"value": doi_record.get("URL", "")},
            "external-id-relationship": "self"
        })
    else:
        # Log a warning if DOI is missing
        logging.warning("DOI missing in record")

    # Process and add ISBN and ISSN
    for key, new_key in [('isbn-type', 'isbn'), ('issn-type', 'issn')]:
        if key in doi_record:
            # Initialize variables for electronic and print IDs
            electronic_id = None
            print_id = None

            # Iterate over each identifier and categorize as electronic or print
            for identifier in doi_record[key]:
                if identifier['type'] == 'electronic':
                    electronic_id = identifier['value']
                elif identifier['type'] == 'print':
                    print_id = identifier['value']

            # Choose electronic ID over print ID if available
            processed_id = electronic_id if electronic_id else print_id
            if processed_id:
                # Append the processed ID to the external-id list
                external_ids.append({
                    "external-id-type": new_key.lower(),
                    "external-id-value": processed_id,
                    "external-id-relationship": "part-of"
                })
    # Add external IDs to the record only if there are valid IDs
    if external_ids:
        record["external-ids"] = {"external-id": external_ids}

    # Return the updated record
    return record


def add_titles(record, doi_record):
    if "title" in doi_record and doi_record["title"]:
        record.setdefault("title", {})["title"] = {
            "value": doi_record["title"]}

    if "subtitle" in doi_record and doi_record["subtitle"]:
        record.setdefault("title", {})["subtitle"] = {
            "value": doi_record["subtitle"]}

    # journal-title is overloaded in the Orcid schema to mean container-title
    if "container-title" in doi_record and doi_record["container-title"]:
        record["journal-title"] = {"value": doi_record["container-title"]}


def add_contributors(record, doi_record):
    contributor_roles = ['author', 'editor']  # Extend this list as needed
    contributors = []

    for role in contributor_roles:
        if role in doi_record:
            for contributor_info in doi_record[role]:
                given_name = contributor_info.get("given", "").strip()
                family_name = contributor_info.get("family", "").strip()
                credit_name = f"{family_name}, {given_name}".strip(', ')

                contributor = {"credit-name": {"value": credit_name}}

                # Add contributor role and sequence if available
                contributor_attributes = {}
                contributor_attributes["contributor-role"] = role
                if "sequence" in contributor_info:
                    contributor_attributes["contributor-sequence"] = contributor_info["sequence"]

                if contributor_attributes:
                    contributor["contributor-attributes"] = contributor_attributes

                # Extracting ORCID ID
                orcid_url = contributor_info.get("ORCID")
                if orcid_url:
                    orcid_id = orcid_url.split('/')[-1]
                    contributor["contributor-orcid"] = {
                        "uri": f"https://orcid.org/{orcid_id}",
                        "path": orcid_id,
                        "host": "orcid.org"
                    }

                if credit_name or orcid_id:  # Only add if there is a contributor name or Orcid ID
                    contributors.append(contributor)

    if contributors:
        record["contributors"] = {'contributor': contributors}


def extract_orcid_dois(account_info):
    """Get all the dois claimed by the user
    :param account_info: User orcid account info
    :return: List of extracted DOIs
    """
    extracted_dois = []

    headers = {
        "Accept": "application/vnd.orcid+json",
        "Authorization": "Bearer " + account_info["access_token"],
    }

    try:
        response = requests.get(get_app_config("ORCID_MEMBER_URL") + account_info["orcid"] + "/works",
                                headers=headers, verify=False)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.exception("Error fetching ORCID works: %s", e)
        raise exceptions.APIConnectionException(e)

    if response.status_code == 200:
        res_json = response.json()

        if "group" in res_json:
            works = res_json["group"]

            for work_loc in works:
                if "external-ids" in work_loc:
                    if "external-id" in work_loc["external-ids"]:
                        ids_loc = work_loc["external-ids"]["external-id"]
                        for id_loc in ids_loc:
                            try:
                                id_type = id_loc["external-id-type"]
                                id_val = id_loc["external-id-value"]

                                if id_type.upper() == "DOI" and isinstance(id_val, str):
                                    extracted_dois.append(id_val.casefold())
                            except AttributeError as e:
                                logging.warning(
                                    f"Malformed DOI data encountered: {e}")
    else:
        logging.error(
            f"API returns error. Status Code : {response.status_code} - Message : {response.text}")

    return extracted_dois


def create_orcid_claim_json(doi_record, return_dict=False):
    """
    Convert doi record to Orcid json record to claim.
    :param doi_record: doi record.
    :return: ORCID record in JSON format, or None if an error occurs.
    """
    try:

        # Initialize an empty ORCID record
        orcid_record = {}

        # Fetch and add citation
        citation_bibtex = fetch_citation_bibtex(doi_record['DOI'])
        if citation_bibtex:
            orcid_record['citation'] = {
                'citation-type': 'bibtex',
                'citation-value': citation_bibtex
            }

        # Add external IDs (DOI, ISSN, ISBN)
        add_external_ids(orcid_record, doi_record)

        # Add titles (title, subtitle, journal title)
        add_titles(orcid_record, doi_record)

        # Add contributors (authors, editors, etc.)
        add_contributors(orcid_record, doi_record)

        # Add publication date
        add_pub_date(orcid_record, doi_record)

        if return_dict:
            return orcid_record

        # Convert the ORCID record to JSON format
        return json.dumps(orcid_record)

    except Exception as e:
        logging.error(f"Error in creating ORCID JSON item: {e}", exc_info=True)
        return None
