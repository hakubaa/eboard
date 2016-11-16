from flask import redirect, url_for
from . import auth

@auth.app_errorhandler(404)
def page_not_found(e):
    # return redirect(url_for("auth.login")), 404

@auth.app_errorhandler(500)
def internal_server_error(e):
    # return redirect(url_for("auth.login")), 500
