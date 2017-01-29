from flask import url_for

from app import db
from app.bookmarks.models import Bookmark

from .base import ApiTestCase

class AddBookmarkTest(ApiTestCase):
    
    def test_for_creating_new_bookmark_with_post_request(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.bookmark_create", 
                                            username="Test"),  
                                    data=dict(title="First Bookmark"))
        self.assertEqual(response.status_code, 201)
        bookmark = db.session.query(Bookmark).one()
        self.assertEqual(bookmark.title, "First Note")

    # def test_for_returning_Bad_Request_when_no_note_title(self):
    #     user = self.create_user(name="Test")
    #     project = user.add_project(name="Test Project", 
    #                                deadline=datetime(2015, 1, 1, 0, 0))
    #     self.login(name="Test")
    #     response = self.client.post(url_for("api.project_note_create", 
    #                                         username="Test", 
    #                                         project_id=project.id),  
    #                                 data=dict(name="First Note"))
    #     self.assertEqual(response.status_code, 400)

    # def test_create_note_returns_Not_Found_when_invalid_project_id(self):
    #     user = self.create_user(name="Test")
    #     project = user.add_project(name="Test Project", 
    #                                deadline=datetime(2015, 1, 1, 0, 0))
    #     self.login(name="Test")
    #     response = self.client.post(url_for("api.project_note_create", 
    #                                         username="Test",
    #                                         project_id=project.id+1),
    #                                 data=dict(title="First Note"))
    #     self.assertEqual(response.status_code, 404)
    #     self.assertEqual(db.session.query(Note).count(), 0)

    # def test_post_request_returns_URI_to_new_note(self):
    #     user = self.create_user(name="Test")
    #     project = user.add_project(name="Test Project", 
    #                                deadline=datetime(2015, 1, 1, 0, 0))
    #     self.login(name="Test")
    #     response = self.client.post(url_for("api.project_note_create", 
    #                                         username="Test", 
    #                                         project_id=project.id),  
    #                                 data=dict(title="First Milestone"))
    #     self.assertEqual(response.status_code, 201)
    #     note = project.notes[0]
    #     self.assertIn(url_for("api.project_note_get", username="Test", 
    #                           note_id=note.id, project_id=project.id), 
    #                   response.location)