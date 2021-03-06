import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET KEY") or "skr#$%skdjf3$^23123r$^kgvdt^765"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")
    SQLALCHEMY_ECHO = True
    TEMPLATES_AUTO_RELOAD = True

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SERVER = "http://localhost:5000"

class ProductionConfig(Config):
    SERVER = "http://eboard-jago.rhcloud.com"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
        os.environ.get("OPENSHIFT_DATA_DIR", ""), "data-dev.sqlite")
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SERVER_NAME = "localhost"
    SERVER = "http://localhost:5000"
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = True


config = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "default": DevelopmentConfig,
        "testing": TestingConfig
        }

