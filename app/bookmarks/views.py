from flask import (
    render_template, request, redirect, url_for, flash
)
from flask_login import login_required, current_user

from app.bookmarks import bookmarks
from app.bookmarks.forms import BookmarkForm, ItemForm
from app import db
from app.models import User, Bookmark, Item


@bookmarks.route("/<username>", methods=["GET", "POST"])
@login_required
def index(username):
    user = db.session.query(User).filter_by(username=username).one_or_none()
    if not user:
        flash("There is no user with given username or "
              "his/her profile is private.", "info")
        return redirect(url_for("bookmarks.index", 
                                username=current_user.username))
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

    page = int(request.args.get("page", 1))
    pagination = user.bookmarks.order_by(Bookmark.created.asc()).\
                     paginate(page, per_page = 15, error_out=False)  

    return render_template("bookmarks/index.html", user=user, form=form,
                           pagination=pagination)


@bookmarks.route("/<username>/bk/<bookmark_id>", methods=["GET", "POST"])
@login_required
def items(username, bookmark_id):
    user = db.session.query(User).filter_by(username=username).one_or_none()
    if not user:
        flash("There is no user with given username or "
              "his/her profile is private.", "info")
        return redirect(url_for("bookmarks.index", 
                                username=current_user.username))
    bookmark = db.session.query(Bookmark).join(User).filter(User.id == user.id,
                   Bookmark.id == bookmark_id).one_or_none()
    if not bookmark:
        flash("Bookmark doesn't exist.")
        return redirect(url_for("bookmarks.index", username=username))        
    form = ItemForm(request.form)
    if request.method == "POST":
        if current_user != user:
            flash("You can't create new item for other user.", "danger")
        else:
            if form.validate_on_submit():
                data = request.form.to_dict()
                bookmark.add_item(value=data["value"], 
                                  desc=data.get("desc", None))
            flash("Item has been successfully addded to the bookmark.", "success")
            return redirect(url_for("bookmarks.items", username=username,
                                    bookmark_id=bookmark.id)) 

    page = int(request.args.get("page", 1))
    pagination = bookmark.items.order_by(Item.created.asc()).\
                     paginate(page, per_page = 15, error_out=False)  

    return render_template("bookmarks/items.html", user=user, form=form,
                           bookmark=bookmark, pagination=pagination)