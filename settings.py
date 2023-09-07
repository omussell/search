import os
import logging as logger

SECRET_KEY = os.environ.get("SECRET_KEY")

SESSION_LIFETIME = 3600*24*30

BASE_API_URL = os.environ.get("BASE_API_URL", "https://api.crossref.org/")

ORCID_CLIENT_ID = os.environ.get("ORCID_CLIENT_ID", "invalid")
ORCID_CLIENT_SECRET = os.environ.get("ORCID_CLIENT_SECRET", "invalid")

ORCID_SITE = os.environ.get("ORCID_SITE", "https://api.orcid.org")
ORCID_AUTHORIZE_URL = os.environ.get("ORCID_AUTHORIZE_URL", "https://orcid.org/oauth/authorize")
ORCID_TOKEN_URL = os.environ.get("ORCID_TOKEN_URL", "https://api.orcid.org/oauth/token")
ORCID_MEMBER_URL = os.environ.get("ORCID_MEMBER_URL", "https://api.orcid.org/v3.0/")

try:
    from version import version as APP_VERSION
except ImportError:
    APP_VERSION = "unknown"

print(f"APP_VERSION is set to {APP_VERSION}")
logger.error(f"APP_VERSION is set to {APP_VERSION}")

API_MAILTO = os.environ.get("API_MAILTO", "search@crossref.org")
API_USER_AGENT_NAME = os.environ.get("API_USER_AGENT_NAME", "CrossrefSearch")
API_USER_AGENT = f"{API_USER_AGENT_NAME}/{APP_VERSION}; mailto:{API_MAILTO}"
API_HEADERS = {"User-Agent": API_USER_AGENT}

print(f"API_USER_AGENT is set to {API_USER_AGENT}")
logger.error(f"API_USER_AGENT is set to {API_USER_AGENT}")
