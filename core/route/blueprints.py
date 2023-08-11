from core.route.healthcheck import healthcheck
from core.route.orcid_auth import auth, orcid
from core.route.search import help, home, search


def register_blueprints(app):
    app.register_blueprint(orcid, url_prefix="/orcid")
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(search, url_prefix="/search")
    app.register_blueprint(help, url_prefix="/help")
    app.register_blueprint(home, url_prefix="/")
    app.register_blueprint(healthcheck, url_prefix="/heartbeat")
