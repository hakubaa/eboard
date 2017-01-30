from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_moment import Moment
from config import config
from .momentjs import MomentJS

bootstrap = Bootstrap()
db = SQLAlchemy()
moment = Moment()

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"


# Default date format used by models
dtformat_default = "%Y-%m-%d %H:%M"


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.jinja_env.globals["momentjs"] = MomentJS
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)

    # from .main import main as main_blueprint
    # app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from .eboard import eboard as eboard_blueprint
    app.register_blueprint(eboard_blueprint, url_prefix = "/eboard")

    from .mail import mail as mail_blueprint
    app.register_blueprint(mail_blueprint, url_prefix = "/mail")

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix = "/api")

    return app
