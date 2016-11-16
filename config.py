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
    # SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")
    UPLOAD_FOLDER = "files/books"
    SERVER = "http://localhost:5000"

class ProductionConfig(Config):
    SERVER = "http://eboard-jago.rhcloud.com"

config = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "default": ProductionConfig
        }

