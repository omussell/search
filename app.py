import logging.handlers
import os

from flask import Flask, flash, render_template, request, send_from_directory
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

import settings
from core import constants, static_assets, utils
from core.route import blueprints
from core.utils import get_request_data

# Create APP
app = Flask(__name__)

# Apply the ProxyFix middleware
# Here, x_for=1 means we trust one reverse proxy (one hop)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

csrf = CSRFProtect(app)

app.config["CORS_HEADERS"] = "Content-Type"
cors_config = {
    "origins": ["https://assets.crossref.org", "https://search-cdn.production.crossref.org"],
}
CORS(app, resources={r"/*": cors_config})

utils.set_base_path(app.root_path)
app.config.from_object(settings)
utils.set_app_config(app.config)

app.config["SECRET_KEY"] = utils.get_app_config("SECRET_KEY")
app.config["SESSION_COOKIE_NAME"] = "crossref_session"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = utils.get_app_config("SESSION_LIFETIME")

blueprints.register_blueprints(app)

# Fingerprint static files so we can serve them with long-lived cache headers.
# Hashed names come from the manifest; content changes produce a new filename.
static_assets.build_static_manifest(app.static_folder)
app.jinja_env.globals["static_url"] = static_assets.static_url


def _serve_static(filename):
    original = static_assets.resolve_hashed_filename(filename)
    if original is None:
        return send_from_directory(app.static_folder, filename)
    response = send_from_directory(app.static_folder, original)
    response.cache_control.no_cache = None
    response.cache_control.public = True
    response.cache_control.max_age = 31536000
    response.cache_control.immutable = True
    return response


app.view_functions["static"] = _serve_static


# Logger configuration
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger(__name__)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

rootLogger.setLevel(logging.INFO)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
formatter = logging.Formatter("[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s","%m-%d %H:%M:%S")

@app.errorhandler(400)
def error_400(e):
    app.logger.error(f"400 error occurred. Requested URL: {request.url} Request data: {get_request_data()}")
    app.logger.error(e)
    return render_template("400.html"), 400


@app.errorhandler(401)
def error_401(e):
    app.logger.error(f"401 error occurred. Requested URL: {request.url}")
    app.logger.error(e)
    return render_template("401.html"), 401


@app.errorhandler(404)
def error_404(e):
    app.logger.error(f"404 error occurred. Requested URL: {request.url}")
    return render_template("404.html"), 404


@app.errorhandler(500)
def error_500(e):
    app.logger.error(f"500 error occurred. Requested URL: {request.url} Request data: {get_request_data()}")
    return render_template("500.html"), 500


@app.context_processor
def user_info():
    signed_in, info, session_expired = utils.signed_in_info()
    context_dict = {"signed_in": signed_in, "orcid_info": info}
    if session_expired:
        flash(constants.ORCID_SESSION_EXPIRED, constants.MESSAGE_TYPE_WARN)
    return context_dict


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 8000), debug=os.environ.get("DEBUG", False))
