from flask import Blueprint

bookmarks = Blueprint("bookmarks", __name__)

from app.bookmarks import views
