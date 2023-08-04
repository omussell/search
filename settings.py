import os
import dotenv

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))

SECRET_KEY = os.environ.get("SECRET_KEY")

SESSION_LIFETIME = 3600*24*30

ORCID_CLIENT_ID = os.environ['ORCID_CLIENT_ID']
ORCID_CLIENT_SECRET = os.environ['ORCID_CLIENT_SECRET']

ORCID_SITE = os.environ.get('ORCID_SITE', "https://api.orcid.org")
ORCID_AUTHORIZE_URL = os.environ.get("ORCID_AUTHORIZE_URL", "https://orcid.org/oauth/authorize")
ORCID_TOKEN_URL = os.environ.get("ORCID_TOKEN_URL", "https://api.orcid.org/oauth/token")
ORCID_MEMBER_URL = os.environ.get("ORCID_MEMBER_URL", "https://api.orcid.org/v3.0/")

