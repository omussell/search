import re

CONSENT_COOKIE_KEY = "crossref-consent"
CONSENT_COOKIE_VALUE = """By using the Crossref website you have agreed to our cookie policy."""

# URLs
BASE_API_URL = "https://api.crossref.org/"
WORKS_API_URL = BASE_API_URL + "works"
FUNDERS_API_URL = BASE_API_URL + "funders"
FUNDER_WORKS_API_URL = BASE_API_URL + "funders/{0}/works"
FUNDER_INFO_API_URL = BASE_API_URL + "funders/{0}"
JOURNALS_API_URL = BASE_API_URL + "journals/{0}/works"

# Categories
CATEGORY_HELP = "help"
CATEGORY_WORKS = "works"
CATEGORY_FUNDERS = "funders"
CATEGORY_REFERENCES = "references"

# Constant Values
ROWS_PER_PAGE = 20
MAX_ROWS = 1000
PAGINATION_PAGE_LIMIT = 10

REQUEST_TIME_OUT = 55  # in seconds

MIN_MATCH_SCORE = 75
MIN_MATCH_TERMS = 3
MAX_MATCH_TEXTS = 1000

MESSAGE_TYPE_ERROR = "error"
MESSAGE_TYPE_INFO = "info"
MESSAGE_TYPE_WARN = "warn"

SEARCH_TYPE_DOI = "doi"
SEARCH_TYPE_ISSN = "issn"
SEARCH_TYPE_ORCID = "orcid"

# Exceptions
API_REQUEST_ERROR = "Could not connect to Crossref REST API"
UNKNOWN_ERROR = "Unknown error occurred "

# ORCID Authentication
ORCID_REDIRECT_URL = "auth/orcid/callback?token="

# Session Constants
SESSION_ORCID = 'orcid'
ORCID_INFO = 'orcid_info'
ACCESS_TOKEN = 'access_token'
USER_NAME = 'user_name'
EXPIRES_AT = 'expires_at'

# Messages
ORCID_SESSION_EXPIRED = "You have been signed out of ORCID"

# Regex
DOI = r"(?P<id>10\.\S+/\S+)$"
DOI_REGEX = re.compile(DOI, re.IGNORECASE)
ISSN = r'^\d{4}-\d{3}(\d|X|x){1}$'
ISSN_REGEX = re.compile(ISSN, re.IGNORECASE)
ORCID = r"^[0-9]{4}-[0-9]{4}-[0-9]{4}-\d{3}[\dX]$"
ORCID_REGEX = re.compile(ORCID)
