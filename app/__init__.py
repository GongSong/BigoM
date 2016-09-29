from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bootstrap import Bootstrap
from flask_wtf.csrf import CsrfProtect
from flask_moment import Moment
from config import Config
from flask import redirect

db = SQLAlchemy()
bootstrap = Bootstrap()
moment = Moment()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)
    csrf = CsrfProtect(app)

    db.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)

    @app.route('/')
    def index():
        return redirect('host/hostlist')

    from .host import host as host_blueprint
    csrf.exempt(host.views.postlog)
    app.register_blueprint(host_blueprint, url_prefix='/host')

    return app
