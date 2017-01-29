from app import db

from tests.base import EBoardTestCase

from app.bookmarks.models import Bookmark, Item


class BookmarkTest(EBoardTestCase):

    def test_for_adding_item_to_bookmark(self):
        bookmark = Bookmark(title="My First Bookmark")
        db.session.add(bookmark)
        db.session.commit()
        bookmark.add_item(value="eboard@jago.com", desc="He is the boss.")
        self.assertEqual(db.session.query(Item).count(), 1)
        self.assertEqual(len(bookmark.items), 1)

    def test_add_item_accepts_instance_of_item(self):
        bookmark = Bookmark(title="My Second Bookmark")
        item = Item(value="eboard@jago.com", desc="He is the boss.")
        db.session.add(bookmark)
        db.session.add(item)
        db.session.commit()
        bookmark.add_item(item)
        self.assertEqual(len(bookmark.items), 1)
        self.assertEqual(bookmark.items[0].value, item.value)

    def test_add_item_returns_newly_created_item(self):
        bookmark = Bookmark(title="My Third Bookmark")
        db.session.add(bookmark)
        db.session.commit()
        item = bookmark.add_item(value="eboard@jago.com", 
                                 desc="He is the boss.")
        item_db = bookmark.items[0]
        self.assertEqual(item, item_db)

    def test_for_preventing_commit_in_add_item(self):
        bookmark = Bookmark(title="My Fourth Bookmark")
        db.session.add(bookmark)
        db.session.commit()
        item = bookmark.add_item(value="eboard@jago.com", 
                                 desc="He is the boss.",
                                 commit=False)
        db.session.rollback()
        self.assertEqual(db.session.query(Item).count(), 0)
        self.assertEqual(len(bookmark.items), 0)

    def test_for_removing_item_from_bookmark(self):
        bookmark = Bookmark(title="My 5th Bookmark")
        db.session.add(bookmark)
        db.session.commit()
        item = bookmark.add_item(value="eboard@jago.com", 
                                 desc="He is the boss.",
                                 commit=False)
        bookmark.remove_item(item)
        self.assertEqual(len(bookmark.items), 0)
        self.assertEqual(db.session.query(Item).count(), 0)

    def test_add_items_to_bookmark_with_update_method(self):
        bookmark = Bookmark(title="My 6th Bookmark")
        db.session.add(bookmark)
        db.session.commit()
        item0 = bookmark.add_item(value="eboard@jago.com", 
                                  desc="The master of the universe.")
        item1 = Item(value="john@jago.com", desc="The employee of the year.")
        item2 = Item(value="kate@jago.com", desc="Nice, nice indeed.")
        bookmark.update(items=[item1, item2])
        self.assertEqual(len(bookmark.items), 3)
        self.assertCountEqual(bookmark.items, [item0, item1, item2])

    def test_change_bookmarks_title_with_update_method(self):
        bookmark = Bookmark(title="My 8th Bookmark")
        db.session.add(bookmark)
        db.session.commit()
        bookmark.update(title="My 7th Bookmark")
        self.assertEqual(bookmark.title, "My 7th Bookmark")


class ItemTest(EBoardTestCase):

    def test_for_updating_item(self):
        item = Item(value="eboard@jago.com", desc="He is amazing.")
        db.session.add(item)
        db.session.commit()
        item.update({"value": "jago@eboard.com", "desc": "Who is he?"})
        self.assertEqual(item.value, "jago@eboard.com")
        self.assertEqual(item.desc, "Who is he?")