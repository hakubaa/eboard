from flask import (
    render_template, request, redirect, url_for, flash
)
from flask_login import login_required, current_user

from app.bookmarks import bookmarks
from app.bookmarks.forms import BookmarkForm
from app import db
from app.models import User


@bookmarks.route("/<username>", methods=["GET", "POST"])
@login_required
def index(username):
    user = db.session.query(User).filter_by(username=username).one_or_none()
    form = BookmarkForm(request.form)
    if request.method == "POST":
        if current_user != user:
            flash("You can't create new bookmark for other user.", "danger")
        else:
            if form.validate_on_submit():
                data = request.form.to_dict()
                user.add_bookmark(title=data["title"])
            flash("New bookmark has been successfully created.", "success")
            return redirect(url_for("bookmarks.index", username=username))
    return render_template("bookmarks/index.html", user=user, form=form)