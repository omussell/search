import os

SECRET_KEY = os.environ.get("SECRET_KEY")

SESSION_LIFETIME = 3600*24*30

BASE_API_URL = os.environ.get("BASE_API_URL", "https://api.crossref.org/")

ORCID_CLIENT_ID = os.environ.get('ORCID_CLIENT_ID', "invalid")
ORCID_CLIENT_SECRET = os.environ.get('ORCID_CLIENT_SECRET', "invalid")

ORCID_SITE = os.environ.get('ORCID_SITE', "https://api.orcid.org")
ORCID_AUTHORIZE_URL = os.environ.get("ORCID_AUTHORIZE_URL", "https://orcid.org/oauth/authorize")
ORCID_TOKEN_URL = os.environ.get("ORCID_TOKEN_URL", "https://api.orcid.org/oauth/token")
ORCID_MEMBER_URL = os.environ.get("ORCID_MEMBER_URL", "https://api.orcid.org/v3.0/")

