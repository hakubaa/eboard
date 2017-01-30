from flask import url_for

from app.models import User, Bookmark, Item
from app.bookmarks.forms import BookmarkForm
from app import db

from tests.base import EBoardTestCase


class IndexPageTest(EBoardTestCase):

    def test_index_page_renders_correct_template(self):
        self.create_user()
        self.login()
        self.client.get(url_for("bookmarks.index", username="Test"))
        self.assert_template_used("bookmarks/index.html")

    def test_for_passing_form_to_template(self):
        self.create_user()
        self.login()
        self.client.get(url_for("bookmarks.index", username="Test"))
        form = self.get_context_variable("form")
        self.assertIsInstance(form, BookmarkForm)

    def test_post_request_creates_new_bookmark(self):
        self.create_user()
        self.login()
        self.client.post(url_for("bookmarks.index", username="Test"),
                         data=dict(title="My 1st Bookmark"))
        self.assertEqual(db.session.query(Bookmark).count(), 1)
        bookmark = db.session.query(Bookmark).first()
        self.assertEqual(bookmark.title, "My 1st Bookmark")

    def test_cannot_create_bookmark_for_other_user(self):
        user1 = self.create_user(name="User1")
        user2 = self.create_user(name="User2")
        self.login(name="User1")
        self.client.post(url_for("bookmarks.index", username="User2"),
                         data=dict(title="My 1st Bookmark"))
        self.assertEqual(db.session.query(Bookmark).count(), 0)
        self.assertEqual(len(user2.bookmarks), 0)