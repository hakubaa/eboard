from flask import url_for

from app.models import User, Bookmark, Item
from app.bookmarks.forms import BookmarkForm, ItemForm
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
        self.assertEqual(user2.bookmarks.count(), 0)

    def test_for_showing_bookmarks_titles(self):
        user = self.create_user()
        bk1 = user.add_bookmark(title="Contacts")
        bk2 = user.add_bookmark(title="Books to read")
        self.login()
        response = self.client.get(url_for("bookmarks.index", username="Test"))
        self.assertIn(bk1.title, response.data.decode())
        self.assertIn(bk2.title, response.data.decode())


class ItemsTestPage(EBoardTestCase):

    def test_renders_proper_template(self):
        user = self.create_user()
        bk = user.add_bookmark(title="Contacts")
        bk.add_item(value="boss@jago.com", desc="Boss")
        bk.add_item(value="ks@jago.com", desc="Master")
        self.login()
        response = self.client.get(url_for("bookmarks.items", username="Test",
                                           bookmark_id=bk.id))
        self.assert_template_used("bookmarks/items.html")

    def test_for_passing_form_to_template(self):
        user = self.create_user()
        bk = user.add_bookmark(title="Contacts")
        self.login()
        response = self.client.get(url_for("bookmarks.items", username="Test",
                                           bookmark_id=bk.id))
        form = self.get_context_variable("form")
        self.assertIsInstance(form, ItemForm)

    def test_post_request_creates_new_item(self):
        user = self.create_user()
        bk = user.add_bookmark(title="Contacts")
        self.login()
        response = self.client.post(url_for("bookmarks.items", username="Test",
                                           bookmark_id=bk.id),
                                    data=dict(value="eboard@jago.com", 
                                              desc="E-Board"))
        self.assertEqual(db.session.query(Item).count(), 1)
        bookmark = db.session.query(Bookmark).first()
        self.assertEqual(bookmark.items.count(), 1)

    def test_cannot_create_item_for_other_user(self):
        user1 = self.create_user(name="User1")
        user2 = self.create_user(name="User2")
        bk = user2.add_bookmark(title="Contacts")
        self.login(name="User1")
        self.client.post(url_for("bookmarks.items", username="User2",
                                 bookmark_id=bk.id),
                         data=dict(value="My 1st Item"))
        self.assertEqual(db.session.query(Item).count(), 0)
        self.assertEqual(bk.items.count(), 0)

    def test_for_showing_items_values(self):
        user = self.create_user()
        bk1 = user.add_bookmark(title="Contacts")
        item1 = bk1.add_item(value="Value 1", desc="Desc. of Value 1")
        item2 = bk1.add_item(value="Value 2", desc="Desc. of Value 2")
        self.login()
        response = self.client.get(url_for("bookmarks.items", username="Test",
                                           bookmark_id=bk1.id))
        self.assertIn(item1.value, response.data.decode())
        self.assertIn(item2.value, response.data.decode())
