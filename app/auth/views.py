from flask import (render_template, redirect, url_for, flash, 
    request, send_from_directory, current_app)
from flask_login import login_user, logout_user, login_required, current_user

from .forms import SignInForm
from ..models import User
from . import auth

import app.mail.views as mail


@auth.route("/login", methods=["GET", "POST"])
@auth.route("/", methods=["GET", "POST"])
def login():
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get("next") or url_for("eboard.index"))
        flash("Invalid username or password.")
    return render_template("auth/login.html", form=form)

@auth.route("/logout")
@login_required
def logout():
    mail.logout_from_imap(current_user.id)
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))
