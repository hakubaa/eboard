from flask import (render_template, redirect, url_for, flash, 
    request, send_from_directory, current_app)
from flask_login import login_user, logout_user, login_required, current_user

from .forms import SignInForm
from ..models import User
from . import auth

from app import login_manager

import app.mail.views as mail


@auth.route("/login", methods=["GET", "POST"])
@auth.route("/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("eboard.index", username=current_user.username))

    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(url_for("eboard.index", username=form.username.data))
    return render_template("auth/login.html", form=form)

@auth.route("/logout")
@login_required
def logout():
    mail.logout_from_imap()
    logout_user()
    return redirect(url_for("auth.login"))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("auth.login"))