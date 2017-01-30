from flask import url_for

from app import db
from app.bookmarks.models import Bookmark, Item
from app.models import User

from .base import ApiTestCase


class GetBookmarksTest(ApiTestCase):

    def test_get_request_returns_list_of_bookmarks(self):
        user = self.create_user(name="Test")
        user.add_bookmark(title="1st Bookmark")
        user.add_bookmark(title="My 2nd Bookmark")
        self.login(name="Test")
        response = self.client.get(url_for("api.bookmarks", username="Test"))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "1st Bookmark")

    def test_for_presence_of_uri_in_bookmark_info(self):
        user = self.create_user(name="Test")
        bookmark1 = user.add_bookmark(title="1st Bookmark")
        bookmark2 = user.add_bookmark(title="My 2nd Bookmark")
        self.login(name="Test")
        response = self.client.get(url_for("api.bookmarks", username="Test"))
        uris = [ bk["uri"] for bk in response.json ]
        self.assertIn(url_for("api.bookmark_get", username="Test", 
                              bookmark_id=bookmark1.id), uris)
        self.assertIn(url_for("api.bookmark_get", username="Test", 
                              bookmark_id=bookmark2.id), uris)


class AddBookmarkTest(ApiTestCase):
    
    def test_for_creating_new_bookmark_with_post_request(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.bookmark_create", 
                                            username="Test"),  
                                    data=dict(title="First Bookmark"))
        self.assertEqual(response.status_code, 201)
        bookmark = db.session.query(Bookmark).one()
        self.assertEqual(bookmark.title, "First Bookmark")

    def test_for_returning_Bad_Request_when_no_bookmark_title(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.bookmark_create", 
                                            username="Test"),  
                                    data=dict(name="First Bookmark"))
        self.assertEqual(response.status_code, 400)

    def test_post_request_returns_URI_to_new_bookmark(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.bookmark_create", 
                                            username="Test"),  
                                    data=dict(title="First Bookmark"))
        self.assertEqual(response.status_code, 201)
        bookmark = user.bookmarks[0]
        self.assertIn(url_for("api.bookmark_get", username="Test", 
                              bookmark_id=bookmark.id), 
                      response.location)


class GetBookmarkTest(ApiTestCase):

    def test_get_request_returns_information_about_bookmark(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="Contacts")
        self.login(name="Test")
        response = self.client.get(url_for("api.bookmark_get", 
                                           username="Test",
                                           bookmark_id=bookmark.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["title"], bookmark.title)

    def test_get_request_returns_Not_Found_for_unknown_bookmark_id(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="Contacts")
        self.login(name="Test")
        response = self.client.get(url_for("api.bookmark_get", 
                                           username="Test", 
                                           bookmark_id=bookmark.id+1))
        self.assertEqual(response.status_code, 404)


class DeleteBookmarkTest(ApiTestCase):

    def test_for_deleting_bookmark_with_delete_request(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        self.login(name="Test")
        response = self.client.delete(url_for("api.bookmark_delete", 
                                              username="Test",
                                              bookmark_id=bookmark.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(user.bookmarks), 0)
        self.assertEqual(db.session.query(Bookmark).count(), 0)

    def test_delete_request_returns_Not_Found_for_unknwon_id(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        self.login(name="Test")
        response = self.client.delete(url_for("api.bookmark_delete", 
                                              username="Test",
                                              bookmark_id=bookmark.id+1))
        self.assertEqual(response.status_code, 404)


class UpdateBookmarkTest(ApiTestCase):

    def test_for_updating_bookmark_with_put_request(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        self.login(name="Test") 
        response = self.client.put(url_for("api.bookmark_edit", 
                                           username="Test", 
                                           bookmark_id=bookmark.id),
                                   data=dict(title="New Title")) 
        self.assertEqual(response.status_code, 204)
        bookmark = db.session.query(User).one().bookmarks[0]
        self.assertEqual(bookmark.title, "New Title")

    def test_put_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        self.login(name="Test") 
        response = self.client.put(url_for("api.bookmark_edit", 
                                           username="Test", 
                                           bookmark_id=bookmark.id+1),
                                   data=dict(title="New Title")) 
        self.assertEqual(response.status_code, 404)


class AddItemTest(ApiTestCase):

    def test_for_creating_new_item_with_post_request(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="My 1st bookmark")
        self.login(name="Test")
        response = self.client.post(url_for("api.item_create", 
                                            username="Test", 
                                            bookmark_id=bookmark.id),  
                                    data=dict(value="eboard@jago.com", 
                                              desc="E-Mail"))
        self.assertEqual(response.status_code, 201)
        item = db.session.query(Item).one()
        self.assertEqual(item.bookmark, bookmark)
        self.assertEqual(item.value, "eboard@jago.com")

    def test_for_returning_Bad_Request_when_no_item_value(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        self.login(name="Test")
        response = self.client.post(url_for("api.item_create", username="Test", 
                                            bookmark_id=bookmark.id),  
                                    data=dict(name="eboard@jago.com"))
        self.assertEqual(response.status_code, 400)

    def test_post_request_returns_URI_to_new_item(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        self.login(name="Test")
        response = self.client.post(url_for("api.item_create", 
                                            username="Test",
                                            bookmark_id=bookmark.id),  
                                    data=dict(value="eboard@jago.com"))
        self.assertEqual(response.status_code, 201)
        item = bookmark.items[0]
        self.assertIn(url_for("api.item_get", username="Test",
                              bookmark_id=bookmark.id, item_id=item.id),
                      response.location)

    def test_post_request_returns_404_when_unknown_bookmark_id(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        self.login(name="Test")
        response = self.client.post(url_for("api.item_create", 
                                            username="Test", 
                                            bookmark_id=bookmark.id+1),  
                                    data=dict(value="eboard@jago.com"))
        self.assertEqual(response.status_code, 404)


class ItemsTest(ApiTestCase):

    def test_get_request_returns_list_of_items(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item1 = bookmark.add_item(value="ja@jago.com", desc="JA")
        item2 = bookmark.add_item(value="ks@jago.com", desc="KS")
        
        self.login(name="Test")
        response = self.client.get(url_for("api.items", username="Test",
                                           bookmark_id=bookmark.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        ivalues = [ item["value"] for item in data ]
        self.assertCountEqual(ivalues, [item1.value, item2.value])

    def test_for_presence_of_uri_in_item_info(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item1 = bookmark.add_item("ja@jago.com", "JA")
        item2 = bookmark.add_item("ks@jago.com", "KS")
        self.login(name="Test")
        response = self.client.get(url_for("api.items", username="Test",
                                           bookmark_id=bookmark.id))
        data = response.json
        items_uri = [ item["uri"] for item in data ]
        self.assertIn(url_for("api.item_get", username="Test", 
                              bookmark_id=bookmark.id, item_id=item1.id), 
                      items_uri)
        self.assertIn(url_for("api.item_get", username="Test", 
                              bookmark_id=bookmark.id, item_id=item2.id), 
                      items_uri)

    def test_returns_404_for_unknown_bookmark_id(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item1 = bookmark.add_item("ja@jago.com", "JA")
        self.login(name="Test")
        response = self.client.get(url_for("api.items", username="Test",
                                           bookmark_id=bookmark.id+1))
        self.assertEqual(response.status_code, 404)


class GetItemTest(ApiTestCase):

    def test_get_request_returns_information_about_item(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item = bookmark.add_item(value="eboard@jago.com", desc="Boss")
        self.login(name="Test")
        response = self.client.get(url_for("api.item_get", 
                                           username="Test",
                                           bookmark_id=bookmark.id, 
                                           item_id=item.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["value"], item.value)
        self.assertEqual(data["desc"], item.desc)

    def test_get_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item = bookmark.add_item(value="eboard@jago.com", desc="Boss")
        self.login(name="Test")
        response = self.client.get(url_for("api.item_get", 
                                           username="Test",
                                           bookmark_id=bookmark.id, 
                                           item_id=item.id+1))
        self.assertEqual(response.status_code, 404)

    def test_get_request_returns_404_for_invalid_bookmark_id(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item = bookmark.add_item(value="eboard@jago.com", desc="Boss")
        self.login(name="Test")
        response = self.client.get(url_for("api.item_get", 
                                           username="Test",
                                           bookmark_id=bookmark.id+1, 
                                           item_id=item.id))
        self.assertEqual(response.status_code, 404)
        

class UpdateItemTest(ApiTestCase):
    
    def test_for_updating_item_with_put_request(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item = bookmark.add_item(value="eboard@jago.com", desc="Boss")
        self.login(name="Test") 
        response = self.client.put(url_for("api.item_edit", username="Test", 
                                           bookmark_id=bookmark.id, 
                                           item_id=item.id),
                                   data=dict(value="jago.com", desc="JAGO"))
        self.assertEqual(response.status_code, 204)
        item = user.bookmarks[0].items[0]
        self.assertEqual(item.value, "jago.com")
        self.assertEqual(item.desc, "JAGO")

    def test_put_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item = bookmark.add_item(value="eboard@jago.com", desc="Boss")
        self.login(name="Test") 
        response = self.client.put(url_for("api.item_edit", username="Test", 
                                           bookmark_id=bookmark.id, 
                                           item_id=item.id+1),
                                   data=dict(value="jago.com", desc="JAGO"))
        self.assertEqual(response.status_code, 404)


class DeleteItemTest(ApiTestCase):

    def test_for_deleting_item_with_delete_request(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item = bookmark.add_item(value="eboard@jago.com", desc="JAGO")
        self.login(name="Test")
        response = self.client.delete(url_for("api.item_delete", 
                                              username="Test",
                                              bookmark_id=bookmark.id, 
                                              item_id=item.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(bookmark.items), 0)
        self.assertEqual(db.session.query(Item).count(), 0)

    def test_delete_request_returns_Not_Found_for_unknwon_id(self):
        user = self.create_user(name="Test")
        bookmark = user.add_bookmark(title="E-Mails")
        item = bookmark.add_item(value="eboard@jago.com", desc="JAGO")
        self.login(name="Test")
        response = self.client.delete(url_for("api.item_delete", 
                                              username="Test",
                                              bookmark_id=bookmark.id, 
                                              item_id=item.id+1))
        self.assertEqual(response.status_code, 404)