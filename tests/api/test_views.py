import json
from datetime import datetime

from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from app.models import User, Task


class ApiTestCase(TestCase):

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_user(self, name="Test", password="test"):
        user = User(username=name, password=password)
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, name="Test", password="test"):
        return self.client.post(url_for("auth.login"), data=dict(
            username=name,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get(url_for("auth.logout"), follow_redirects=True)


################################################################################

class TestApiAccess(ApiTestCase):
    '''
    Test access restriction. access_required decorator is applied to all views.
    Use /<username>/tasks as sample view.
    '''
    def test_returns_Unauthorized_for_not_logged_user(self):
        self.create_user(name="Test")
        response = self.client.get(url_for("api.tasks", username="Test"))
        self.assertEqual(response.status_code, 401)

    def test_returns_Not_Found_for_unknown_user(self):
        self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.get(url_for("api.tasks", username="unknown"))
        self.assertEqual(response.status_code, 404)

    def test_returns_Not_Found_for_user_with_private_profile(self):
        user = self.create_user(name="Test")
        db.session.commit()
        self.create_user(name="Terminator")
        self.login(name="Terminator")
        response = self.client.get(url_for("api.tasks", username="Test"))
        self.assertEqual(response.status_code, 404)

    def test_returns_OK_when_access_user_with_public_profile(self):
        user = self.create_user(name="Test") 
        user.public = True
        db.session.commit()
        self.create_user(name="Terminator")
        self.login(name="Terminator")
        response = self.client.get(url_for("api.tasks", username="Test"))
        self.assertEqual(response.status_code, 200)

    def test_returns_OK_when_access_own_resources(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.get(url_for("api.tasks", username="Test"))
        self.assertEqual(response.status_code, 200)


class TestApiUser(ApiTestCase):

    def test_returns_json_response_for_get_request(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.get(url_for("api.user_index", username="Test"))
        data = response.json
        self.assertEqual(data["username"], "Test")

    def test_creates_uri_for_tasks(self):
        user = self.create_user(name="Test")
        task1 = user.add_task(title="First Task", 
                              deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.user_index", username="Test"))
        data = response.json
        self.assertEqual(data["tasks"][0]["uri"], "/Test/tasks/" + str(task1.id))

    def test_creates_uri_for_projects(self):
        user = self.create_user(name="Test")
        proj1 = user.add_project(name="First Project", 
                                 deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.user_index", username="Test"))
        data = response.json
        self.assertEqual(data["projects"][0]["uri"], "/Test/projects/" + str(proj1.id))        

    def test_creates_uri_for_notes(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="First Note", body="Interesting!!!")
        self.login(name="Test")
        response = self.client.get(url_for("api.user_index", username="Test"))
        data = response.json
        self.assertEqual(data["notes"][0]["uri"], "/Test/notes/" + str(note.id))        

    def test_creates_user_with_post_request_and_return_201(self):
        response = self.client.post(url_for("api.user_create"), 
                                    data=dict(username="Test", password="test",
                                              password2="test"))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(db.session.query(User).count(), 1)
        self.assertEqual(db.session.query(User).one().username, "Test")

    def test_create_user_returns_Bad_Request_when_no_username(self):
        response = self.client.post(url_for("api.user_create"), 
                                    data=dict(name="Test", password="test",
                                              password2="test"))
        self.assertEqual(response.status_code, 400)    

    def test_create_user_returns_Bad_Request_when_invalid_passwords(self):
        response = self.client.post(url_for("api.user_create"), 
                                    data=dict(username="Test", password="test",
                                              password2="sets"))
        self.assertEqual(response.status_code, 400)      

    def test_create_user_returns_Conflict_when_username_is_occupied(self):
        self.create_user(name="Test")
        response = self.client.post(url_for("api.user_create"), 
                                    data=dict(username="Test", password="test",
                                              password2="test"))
        self.assertEqual(response.status_code, 409)                

    def test_updates_client_with_put_request(self):
        user = self.create_user(name="Test", password="test")
        self.login(name="Test")
        response = self.client.put(url_for("api.user_edit", username="Test"),
                                   data=dict(public=True, new_password="sets",
                                             new_password2="sets"))
        self.assertEqual(response.status_code, 200)
        user = db.session.query(User).one()
        self.assertTrue(user.verify_password("sets"))
        self.assertTrue(user.public)

    def test_deletes_client_with_delete_request(self):
        user = self.create_user(name="Test", password="test")
        self.login(name="Test")
        response = self.client.delete(url_for("api.user_delete", username="Test"),
                                      data=dict(password="test"))
        self.assertEqual(response.status_code, 410)
        self.assertEqual(db.session.query(User).count(), 0)

    def test_delete_request_returns_Bad_Request_when_invalid_password(self):
        user = self.create_user(name="Test", password="test")
        self.login(name="Test")
        response = self.client.delete(url_for("api.user_delete", username="Test"),
                                      data=dict(password="sets"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(db.session.query(User).count(), 1)


class TestApiTasks(ApiTestCase):
    pass

class TestApiNotes(ApiTestCase):
    pass

class TestApiProjects(ApiTestCase):
    pass

class TestApiMilestones(ApiTestCase):
    pass