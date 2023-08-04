from core.route.search import search, help, home
from core.route.orcid_auth import auth, orcid


def register_blueprints(app):
    app.register_blueprint(orcid, url_prefix='/orcid')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(search, url_prefix='/search')
    app.register_blueprint(help, url_prefix='/help')
    app.register_blueprint(home, url_prefix='/')
