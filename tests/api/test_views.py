import json
from datetime import datetime
import unittest

from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from app.models import User, Task, Note, Project, Milestone, Tag, Event

from .base import ApiTestCase

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
        self.assertIn(url_for("api.task_get", username="Test", task_id=task1.id),
                      data["tasks"][0]["uri"])

    def test_creates_uri_for_projects(self):
        user = self.create_user(name="Test")
        proj1 = user.add_project(name="First Project", 
                                 deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.user_index", username="Test"))
        data = response.json
        self.assertIn(url_for("api.project_get", username="Test", 
                              project_id=proj1.id),
                      data["projects"][0]["uri"])

    def test_creates_uri_for_notes(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="First Note", body="Interesting!!!")
        self.login(name="Test")
        response = self.client.get(url_for("api.user_index", username="Test"))
        data = response.json
        self.assertIn(url_for("api.note_get", username="Test", note_id=note.id),
                      data["notes"][0]["uri"])

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
        self.assertEqual(response.status_code, 204)
        user = db.session.query(User).one()
        self.assertTrue(user.verify_password("sets"))
        self.assertTrue(user.public)

    def test_deletes_client_with_delete_request(self):
        user = self.create_user(name="Test", password="test")
        self.login(name="Test")
        response = self.client.delete(url_for("api.user_delete", 
                                              username="Test"),
                                      data=dict(password="test"))
        self.assertEqual(response.status_code, 410)
        self.assertEqual(db.session.query(User).count(), 0)

    def test_delete_request_returns_Bad_Request_when_invalid_password(self):
        user = self.create_user(name="Test", password="test")
        self.login(name="Test")
        response = self.client.delete(url_for("api.user_delete", 
                                              username="Test"),
                                      data=dict(password="sets"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(db.session.query(User).count(), 1)


class TestApiTasks(ApiTestCase):
    
    def test_get_request_returns_list_of_tasks(self):
        user = self.create_user(name="Test")
        user.add_task(title="First Task", deadline=datetime(2015, 1, 1, 0, 0))
        user.add_task(title="Second Task", deadline=datetime(2015, 1, 1, 0 , 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.tasks", username="Test"))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "First Task")

    def test_for_presence_of_uri_in_task_info(self):
        user = self.create_user(name="Test")
        task1 = user.add_task(title="First Task", 
                              deadline=datetime(2015, 1, 1, 0, 0))
        task2 = user.add_task(title="Second Task", 
                              deadline=datetime(2015, 1, 1, 0 , 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.tasks", username="Test"))
        data = response.json
        tasks_uri = [ task["uri"] for task in data ]
        self.assertIn(url_for("api.task_get", username="Test", 
                              task_id=task1.id), tasks_uri)
        self.assertIn(url_for("api.task_get", username="Test", 
                              task_id=task2.id), tasks_uri)

    def test_post_request_creates_new_task(self):
        user = self.create_user(name="Test")
        user.add_task(title="First Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.task_create", username="Test"), 
                                    data=dict(title="Second Task", 
                                              deadline="2016-01-01 00:00",
                                              rubbish="Sd34FDK_"))
        self.assertEqual(response.status_code, 201) # 201 - CREATED ?
        self.assertEqual(db.session.query(Task).count(), 2)
        user = db.session.query(User).one()
        self.assertEqual(user.tasks.count(), 2)
        task_titles = [ task.title for task in user.tasks ]
        self.assertIn("Second Task", task_titles)

    def test_post_request_returns_Bad_Request_when_no_title(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.task_create", username="Test"),
                                    data=dict(deadline="2016-01-01 00:00"))
        self.assertEqual(response.status_code, 400)

    def test_post_request_returns_Bad_Request_when_no_deadline(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.task_create", username="Test"),
                                    data=dict(title="First Task"))
        self.assertEqual(response.status_code, 400)

    def test_post_request_returns_URI_to_new_task_in_location(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.task_create", username="Test"), 
                                    data=dict(title="Second Task", 
                                              deadline="2016-01-01 00:00"))
        self.assertEqual(response.status_code, 201) # 201 - CREATED ?
        task = user.tasks[0]
        self.assertIn(url_for("api.task_get", username="Test", task_id=task.id),
                      response.location)

    def test_create_task_accepts_tags_as_one_string(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.task_create", username="Test"), 
                                    data=dict(title="Second Task", 
                                              deadline="2016-01-01 00:00",
                                              tags="Tag1,Tag2,Tag3"))
        self.assertEqual(db.session.query(Tag).count(), 3)
        task = user.tasks[0]
        self.assertEqual(len(task.tags), 3)

    @unittest.skip
    def test_create_task_accepts_tz_offest_and_converts_deadline_to_utc(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        self.client.post(url_for("api.task_create", username="Test"), 
                         data=dict(title="Test Task", 
                                   deadline="2015-01-01 12:00",
                                   tzoffset="-60"),
                         follow_redirects=True)
        task = user.tasks.one()
        self.assertEqual(task.deadline, datetime(2015, 1, 1, 11, 0))  


class TestApiTaskItem(ApiTestCase):

    def test_get_request_returns_information_about_task(self):
        user = self.create_user(name="Test")
        task = user.add_task(title="First Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.task_get", username="Test",
                                           task_id=task.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["title"], task.title)
        self.assertEqual(data["deadline"], "2015-01-01 00:00")

    def test_get_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        task = user.add_task(title="First Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.task_get", username="Test", 
                                           task_id=task.id+1))
        self.assertEqual(response.status_code, 404)

    def test_for_updating_task_with_put_request(self):
        user = self.create_user(name="Test")
        task = user.add_task(title="First Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test") 
        response = self.client.put(url_for("api.task_edit", username="Test", 
                                           task_id=task.id),
                                   data=dict(title="New Title", complete=True))
        self.assertEqual(response.status_code, 204)
        task = db.session.query(User).one().tasks[0]
        self.assertEqual(task.title, "New Title")
        self.assertTrue(task.complete)

    def test_put_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        task = user.add_task(title="First Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.put(url_for("api.task_edit", username="Test", 
                                           task_id=task.id+1),
                                   data=dict(title="New Title"))
        self.assertEqual(response.status_code, 404)

    def test_for_deleting_task_with_delete_request(self):
        user = self.create_user(name="Test")
        task = user.add_task(title="First Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.delete(url_for("api.task_delete", username="Test",
                                              task_id=task.id))
        self.assertEqual(response.status_code, 204) # 204 - NO CONTENT
        self.assertEqual(user.tasks.count(), 0)
        self.assertEqual(db.session.query(Task).count(), 0)

    def test_delete_request_returns_Not_Found_for_unknwon_id(self):
        user = self.create_user(name="Test")
        task = user.add_task(title="First Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.delete(url_for("api.task_delete", username="Test",
                                              task_id=task.id+1))
        self.assertEqual(response.status_code, 404)

    def test_get_task_from_project(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project", 
                                   deadline=datetime(2019, 1, 1, 0, 0))
        milestone = project.add_milestone(title="New Milestone")
        task = milestone.add_task(title="My First Task!",
                                  deadline=datetime(2019, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.task_get", username="Test",
                                           task_id=task.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["title"], task.title)

    def test_update_task_accepts_tags_as_one_string(self):
        user = self.create_user(name="Test")
        task = user.add_task(title="First Task", 
                             deadline=datetime(2015, 1, 1, 0, 0),
                             tags=["Tag1", "Tag2"])
        self.login(name="Test")
        response = self.client.put(url_for("api.task_edit", username="Test", 
                                           task_id=task.id),
                                   data=dict(tags="Tag3, Tag4, Tag5")) 
        task = db.session.query(User).one().tasks[0]
        self.assertEqual(len(task.tags), 3)
        tags = set([tag.name for tag in task.tags])
        self.assertEqual(tags, {"Tag3", "Tag4", "Tag5"})


class TestApiNotesList(ApiTestCase):
    
    def test_get_request_returns_list_of_notes(self):
        user = self.create_user(name="Test")
        user.add_note(title="First Note", body="Very Important Note!")
        user.add_note(title="Second Note", body="The Most Important Note!!!")
        self.login(name="Test")
        response = self.client.get(url_for("api.notes", username="Test"))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "First Note")

    def test_for_presence_of_uri_in_note_info(self):
        user = self.create_user(name="Test")
        note1 = user.add_note(title="First Note", body="Very Important Note!")
        note2 = user.add_note(title="Second Note", 
                              body="The Most Important Note!!!")
        self.login(name="Test")
        response = self.client.get(url_for("api.notes", username="Test"))
        data = response.json
        notes_uri = [ note["uri"] for note in data ]
        self.assertIn(url_for("api.note_get", username="Test",  
                              note_id=note1.id), 
                      notes_uri)
        self.assertIn(url_for("api.note_get", username="Test", 
                              note_id=note2.id), 
                      notes_uri)

    def test_post_request_creates_new_note(self):
        user = self.create_user(name="Test")
        user.add_note(title="First Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.note_create", username="Test"), 
                                    data=dict(title="Second Note", 
                                              body="Not Important Note!"))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(db.session.query(Note).count(), 2)
        user = db.session.query(User).one()
        self.assertEqual(user.notes.count(), 2)
        note_titles = [ note.title for note in user.notes ]
        self.assertIn("Second Note", note_titles)

    def test_post_request_returns_Bad_Request_when_no_title(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.note_create", username="Test"), 
                                    data=dict(body="Not Important Note!"))
        self.assertEqual(response.status_code, 400)

    def test_post_request_returns_URI_to_new_note(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.notes", username="Test"), 
                                    data=dict(title="Second Note", 
                                              body="Not Important Note!"))
        self.assertEqual(response.status_code, 201) # 201 - CREATED ?
        note = user.notes[0]
        self.assertIn(url_for("api.note_get", username="Test", note_id=note.id),
                      response.location)

    def test_create_note_accepts_tags_as_one_string(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.note_create", username="Test"), 
                                    data=dict(title="Second Note", 
                                              body="Not Important Note!",
                                              tags="Tag1,Tag2,Tag3"))
        self.assertEqual(db.session.query(Tag).count(), 3)
        note = user.notes[0]
        self.assertEqual(len(note.tags), 3)


class TestApiNoteItem(ApiTestCase):

    def test_get_request_returns_information_about_note(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.get(url_for("api.note_get", username="Test",
                                           note_id=note.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["title"], note.title)
        self.assertEqual(data["body"], note.body)

    def test_get_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.get(url_for("api.note_get", username="Test", 
                                           note_id=note.id+1))
        self.assertEqual(response.status_code, 404)

    def test_for_updating_note_with_put_request(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test") 
        response = self.client.put(url_for("api.note_edit", username="Test", 
                                           note_id=note.id),
                                   data=dict(title="New Title", 
                                             body="Not Important.")) 
        self.assertEqual(response.status_code, 204)
        note = db.session.query(User).one().notes[0]
        self.assertEqual(note.title, "New Title")
        self.assertEqual(note.body, "Not Important.")

    def test_put_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.put(url_for("api.note_edit", username="Test", 
                                           note_id=note.id+1),
                                   data=dict(title="New Title"))
        self.assertEqual(response.status_code, 404)

    def test_for_deleting_note_with_delete_request(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.delete(url_for("api.note_delete", username="Test",
                                              note_id=note.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(user.notes.count(), 0)
        self.assertEqual(db.session.query(Note).count(), 0)

    def test_delete_request_returns_Not_Found_for_unknwon_id(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.delete(url_for("api.note_delete", username="Test",
                                              note_id=note.id+1))
        self.assertEqual(response.status_code, 404)

    def test_for_returning_Not_Found_when_deleting_other_user_notes(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="My First Note", body="Hello World!!!")
        user2 = self.create_user(name="Master")
        self.login(name=user2.username)
        response = self.client.delete(url_for("api.note_delete", note_id=note.id,
                                              username=user2.username))
        self.assertEqual(response.status_code, 404)

    def test_update_note_accepts_tags_as_one_string(self):
        user = self.create_user(name="Test")
        note = user.add_note(title="First Note", body="Very Important Note!!!",
                             tags=["Tag1", "Tag2"])
        self.login(name="Test") 
        response = self.client.put(url_for("api.note_edit", username="Test", 
                                           note_id=note.id),
                                   data=dict(tags="Tag3, Tag4, Tag5")) 
        note = db.session.query(User).one().notes[0]
        self.assertEqual(len(note.tags), 3)
        tags = set([tag.name for tag in note.tags])
        self.assertEqual(tags, {"Tag3", "Tag4", "Tag5"})


class TestApiProjects(ApiTestCase):
    
    def test_get_request_returns_list_of_projects(self):
        user = self.create_user(name="Test")
        user.add_project(name="Test Project 1", 
                         deadline=datetime(2018, 1, 1, 0, 0))
        user.add_project(name="Test Project 2", 
                         deadline=datetime(2019, 1, 1, 0, 0))
        user.add_project(name="Test Project 3", 
                         deadline=datetime(2020, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.projects", username="Test"))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 3)
        project_names = [ project["name"] for project in data ]
        self.assertIn("Test Project 1", project_names)
        self.assertIn("Test Project 2", project_names)
        self.assertIn("Test Project 3", project_names)

    def test_for_presence_of_uri_to_project_details(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.projects", username="Test"))
        data = response.json
        self.assertEqual(data[0]["uri"], url_for("api.project_get", 
                                                 username="Test",
                                                 project_id=project.id))

    def test_for_creating_new_project_with_post_request(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.project_create", 
                                            username="Test"),  
                                    data=dict(name="Project Test", 
                                              deadline="2017-01-01 00:00"))
        self.assertEqual(response.status_code, 201)
        project = db.session.query(Project).one()
        self.assertEqual(project.user, user)
        self.assertEqual(project.name, "Project Test")
        self.assertEqual(project.deadline, datetime(2017, 1, 1, 0, 0))

    def test_for_returning_Bad_Request_when_no_project_name(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.projects", username="Test"),
                                    data=dict(nema="Test Project 1"))
        self.assertEqual(response.status_code, 400)

    def test_post_request_returns_URI_to_new_project(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.projects", username="Test"),
                                    data=dict(name="Test Project 1", 
                                              deadline="2017-01-01 00:00"))
        self.assertEqual(response.status_code, 201)
        project = user.projects[0]
        self.assertIn(url_for("api.project_get", username="Test", 
                              project_id=project.id), response.location)
        
class TestApiProject(ApiTestCase):

    def test_get_request_returns_information_about_project(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.project_get", username="Test",
                                           project_id=project.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["name"], project.name)
        self.assertEqual(data["deadline"], "2015-01-01 00:00")

    def test_get_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project",  
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.project_get", username="Test", 
                                           project_id=project.id+1))
        self.assertEqual(response.status_code, 404)

    def test_get_request_accepts_argument_in_query(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project",
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="Frist Milestone")
        task = milestone.add_task(title="First Task", 
                                  deadline=datetime(2016, 1, 1, 0, 0))
        task = milestone.add_task(title="Second Task",
                                  deadline=datetime(2017, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.project_get", username="Test",
                                           project_id=project.id),
                                   data=dict(with_tasks="T"))
        data = response.json
        self.assertEqual(len(data["milestones"][0]["tasks"]), 2)
        tasks = data["milestones"][0]["tasks"]
        self.assertEqual(tasks[0]["title"], "First Task")
        self.assertEqual(tasks[1]["deadline"], "2017-01-01 00:00")


    def test_get_request_returns_uri_of_project_milestones(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        self.login(name="Test")
        response = self.client.get(url_for("api.project_get", username="Test",
                                           project_id=project.id))
        data = response.json
        self.assertEqual(
                data["milestones"][0]["uri"], 
                url_for("api.milestone_get", username="Test", project_id=project.id, 
                        milestone_id=milestone.id)
            )        
          
    def test_for_updating_project_with_put_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test") 
        response = self.client.put(url_for("api.project_edit", 
                                           username="Test", 
                                           project_id=project.id),
                                   data=dict(name="Completed Project", 
                                             complete=True))
        self.assertEqual(response.status_code, 204)
        project = db.session.query(User).one().projects[0]
        self.assertEqual(project.name, "Completed Project")
        self.assertTrue(project.complete)

    def test_put_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.put(url_for("api.project_edit", username="Test", 
                                           project_id=project.id+1),
                                   data=dict(name="New Title"))
        self.assertEqual(response.status_code, 404)

    def test_for_deleting_project_with_delete_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.delete(url_for("api.project_delete", 
                                              username="Test",
                                              project_id=project.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(user.projects.count(), 0)
        self.assertEqual(db.session.query(Project).count(), 0)

    def test_delete_request_returns_Not_Found_for_unknwon_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.delete(url_for("api.project_delete", 
                                              username="Test",
                                              project_id=project.id+1))
        self.assertEqual(response.status_code, 404)
    

class TestApiProjectMilestones(ApiTestCase):
    
    def test_get_request_returns_list_of_milestones(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        project.add_milestone(title="First Milestone")
        project.add_milestone(title="Second Milestone")

        self.login(name="Test")
        response = self.client.get(url_for("api.milestones", username="Test",
                                           project_id=project.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        milestone_names = [ milestone["title"] for milestone in data ]
        self.assertIn("First Milestone", milestone_names)
        self.assertIn("Second Milestone", milestone_names)

    def test_get_request_returns_Not_Found_when_invalid_project_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project",
                                   deadline=datetime(2015, 1, 1, 0 , 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.milestones", username="Test",
                                           project_id=project.id+1))
        self.assertEqual(response.status_code, 404)

    def test_for_presence_of_uri_to_milestones(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")

        self.login(name="Test")
        response = self.client.get(url_for("api.milestones", username="Test",
                                           project_id=project.id))   
        data = response.json
        self.assertEqual(data[0]["uri"], url_for("api.milestone_get", 
                                                 username="Test",
                                                 project_id=project.id, 
                                                 milestone_id=milestone.id))

    def test_for_creating_new_milestone_with_post_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.milestone_create", 
                                            username="Test", project_id=project.id),  
                                    data=dict(title="First Milestone"))
        self.assertEqual(response.status_code, 201)
        milestone = db.session.query(Milestone).one()
        self.assertEqual(milestone.project, project)
        self.assertEqual(milestone.title, "First Milestone")

    def test_for_returning_Bad_Request_when_no_milestone_title(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.milestones", username="Test", 
                                            project_id=project.id),  
                                    data=dict(name="First Milestone"))
        self.assertEqual(response.status_code, 400)

    def test_post_request_returns_URI_to_new_milestone(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.milestone_create", 
                                            username="Test",
                                            project_id=project.id),  
                                    data=dict(title="First Milestone"))
        self.assertEqual(response.status_code, 201)
        milestone = project.milestones[0]
        self.assertIn(url_for("api.milestone_get", username="Test",
                              project_id=project.id, milestone_id=milestone.id),
                      response.location)

    def test_post_request_returns_404_when_unknown_project_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.milestone_create", 
                                            username="Test", 
                                            project_id=project.id+1),  
                                    data=dict(title="First Milestone"))
        self.assertEqual(response.status_code, 404)


################################################################################

class TestApiMilestone(ApiTestCase):

    def test_get_request_returns_information_about_milestone(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone Ever")
        self.login(name="Test")
        response = self.client.get(url_for("api.milestone_get", 
                                           username="Test",
                                           project_id=project.id, 
                                           milestone_id=milestone.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["title"], milestone.title)

    def test_get_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0)) 
        milestone = project.add_milestone(title="First Milestone Ever")
        self.login(name="Test")
        response = self.client.get(url_for("api.milestone_get", 
                                           username="Test", 
                                           project_id=project.id, 
                                           milestone_id=milestone.id+1))
        self.assertEqual(response.status_code, 404)

    def test_get_request_returns_uri_of_tasks_in_milestone(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        task = milestone.add_task(title="First Task", 
                                  deadline=datetime(2014, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.milestone_get",  
                                           username="Test",
                                           project_id=project.id, 
                                           milestone_id=milestone.id))
        data = response.json
        self.assertEqual(
                data["tasks"][0]["uri"], 
                url_for("api.milestone_task_get", username="Test", 
                        project_id=project.id, milestone_id=milestone.id, 
                        task_id=task.id)
            )        
          
    def test_for_updating_milestone_with_put_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="New Milestone")
        self.login(name="Test") 
        response = self.client.put(url_for("api.milestone_edit", username="Test", 
                                           project_id=project.id, 
                                           milestone_id=milestone.id),
                                   data=dict(title="Old Milestone", position=5))
        self.assertEqual(response.status_code, 204)
        milestone = db.session.query(User).one().projects[0].milestones[0]
        self.assertEqual(milestone.title, "Old Milestone")
        self.assertEqual(milestone.position, 5)

    def test_put_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0)) 
        milestone = project.add_milestone(title="New Milestone")
        self.login(name="Test")
        response = self.client.put(url_for("api.milestone_edit", username="Test", 
                                           project_id=project.id, 
                                           milestone_id=milestone.id+1),
                                   data=dict(name="New Name"))
        self.assertEqual(response.status_code, 404)

    def test_for_deleting_milestone_with_delete_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="New Milestone")
        self.login(name="Test")
        response = self.client.delete(url_for("api.milestone_delete", 
                                              username="Test",
                                              project_id=project.id, 
                                              milestone_id=milestone.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(project.milestones), 0)
        self.assertEqual(db.session.query(Milestone).count(), 0)

    def test_delete_request_returns_Not_Found_for_unknwon_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="New Milestone")
        self.login(name="Test")
        response = self.client.delete(url_for("api.milestone_delete", 
                                              username="Test",
                                              project_id=project.id, 
                                              milestone_id=milestone.id+1))
        self.assertEqual(response.status_code, 404)   
        self.assertEqual(db.session.query(Milestone).count(), 1)


class TestApiProjectNotesList(ApiTestCase):
    
    def test_get_request_returns_list_of_notes(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        project.add_note(title="First Note", body="Very Important Note")
        project.add_note(title="Second Note", body="Not Very Importat Note")
        project.add_note(title="Third Note", body="The Least Important Note")
        self.login(name="Test")
        response = self.client.get(url_for("api.project_notes", username="Test",
                                           project_id=project.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 3)
        notes_titles = [ note["title"] for note in data ]
        self.assertIn("First Note", notes_titles)
        self.assertIn("Third Note", notes_titles)

    def test_for_presence_of_uri_to_notes(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note")
        self.login(name="Test")
        response = self.client.get(url_for("api.project_notes", username="Test",
                                           project_id=project.id))   
        data = response.json
        self.assertEqual(data[0]["uri"], url_for("api.project_note_get", 
                                                 username="Test",
                                                 project_id=project.id, 
                                                 note_id=note.id))

    def test_for_creating_new_note_with_post_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.project_note_create", 
                                            username="Test", 
                                            project_id=project.id),  
                                    data=dict(title="First Note"))
        self.assertEqual(response.status_code, 201)
        note = db.session.query(Note).one()
        self.assertEqual(note.project, project)
        self.assertEqual(note.title, "First Note")

    def test_for_returning_Bad_Request_when_no_note_title(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.project_note_create", 
                                            username="Test", 
                                            project_id=project.id),  
                                    data=dict(name="First Note"))
        self.assertEqual(response.status_code, 400)

    def test_create_note_returns_Not_Found_when_invalid_project_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.project_note_create", 
                                            username="Test",
                                            project_id=project.id+1),
                                    data=dict(title="First Note"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(db.session.query(Note).count(), 0)

    def test_post_request_returns_URI_to_new_note(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.post(url_for("api.project_note_create", 
                                            username="Test", 
                                            project_id=project.id),  
                                    data=dict(title="First Milestone"))
        self.assertEqual(response.status_code, 201)
        note = project.notes[0]
        self.assertIn(url_for("api.project_note_get", username="Test", 
                              note_id=note.id, project_id=project.id), 
                      response.location)

    def test_for_moving_milestone_before_another_project(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project",
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        milestone2 = project.add_milestone(title="Second Milestone")
        self.login(name="Test")
        response = self.client.post(url_for("api.milestone_position",
                                            username="Test",
                                            project_id=project.id,
                                            milestone_id=milestone2.id),
                                    data=dict(before=milestone.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            db.session.query(Milestone).filter_by(position=0).one().title, 
            "Second Milestone"
        )
        self.assertEqual(
            db.session.query(Milestone).filter_by(position=1).one().title, 
            "First Milestone"
        )

    def test_for_moving_milestone_after_another_within_project(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project",
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        milestone2 = project.add_milestone(title="Second Milestone")
        self.login(name="Test")
        response = self.client.post(url_for("api.milestone_position",
                                            username="Test",
                                            project_id=project.id,
                                            milestone_id=milestone.id),
                                    data=dict(after=milestone2.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            db.session.query(Milestone).filter_by(position=0).one().title, 
            "Second Milestone"
        )
        self.assertEqual(
            db.session.query(Milestone).filter_by(position=1).one().title, 
            "First Milestone"
        )       

# /api/users/hakubaa/projects/1/milestones/1/position?after=1&before=2 <- POST


class TestApiProjectNoteItem(ApiTestCase):

    def test_get_request_returns_information_about_note(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.get(url_for("api.project_note_get", 
                                           username="Test",
                                           project_id=project.id, 
                                           note_id=note.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["title"], note.title)
        self.assertEqual(data["body"], note.body)

    def test_get_request_returns_Not_Found_for_unknown_note_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.get(url_for("api.project_note_get", 
                                           username="Test", 
                                           project_id=project.id, 
                                           note_id=note.id+1))
        self.assertEqual(response.status_code, 404)

    def test_get_request_returns_Not_Found_for_unknown_project_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.get(url_for("api.project_note_get", 
                                           username="Test", 
                                           project_id=project.id+1, 
                                           note_id=note.id))
        self.assertEqual(response.status_code, 404)

    def test_for_updating_note_with_put_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test") 
        response = self.client.put(url_for("api.project_note_edit", 
                                           username="Test", 
                                           project_id=project.id, 
                                           note_id=note.id),
                                   data=dict(title="New Title", 
                                             body="Not Important."))
        self.assertEqual(response.status_code, 204)
        note = db.session.query(User).one().projects[0].notes[0]
        self.assertEqual(note.title, "New Title")
        self.assertEqual(note.body, "Not Important.")

    def test_put_request_returns_Not_Found_for_unknown_note_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.put(url_for("api.project_note_edit", 
                                           username="Test", 
                                           project_id=project.id, 
                                           note_id=note.id+1),
                                   data=dict(title="New Title", 
                                             body="Not Important."))
        self.assertEqual(response.status_code, 404)

    def test_put_request_returns_Not_Found_for_unknown_project_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.put(url_for("api.project_note_edit", 
                                           username="Test", 
                                           project_id=project.id+1, 
                                           note_id=note.id),
                                   data=dict(title="New Title", 
                                             body="Not Important."))
        self.assertEqual(response.status_code, 404)

    def test_for_deleting_note_with_delete_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.delete(url_for("api.project_note_delete", 
                                              username="Test",
                                              project_id=project.id, 
                                              note_id=note.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(project.notes), 0)
        self.assertEqual(db.session.query(Note).count(), 0)

    def test_delete_request_returns_Not_Found_for_unknwon_note_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.delete(url_for("api.project_note_delete", 
                                              username="Test",
                                              project_id=project.id, 
                                              note_id=note.id+1))
        self.assertEqual(response.status_code, 404)

    def test_delete_request_returns_Not_Found_for_unknwon_project_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note!!!")
        self.login(name="Test")
        response = self.client.delete(url_for("api.project_note_delete", 
                                              username="Test",
                                              project_id=project.id+1, 
                                              note_id=note.id))
        self.assertEqual(response.status_code, 404)


class TestApiProjectMilestoneTasksList(ApiTestCase):

    def test_get_request_returns_list_of_tasks(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        task1 = milestone.add_task(title="First Task", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        task2 = milestone.add_task(title="Second Task", 
                                   deadline=datetime(2018, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.milestone_tasks", 
                                           username="Test",
                                           project_id=project.id, 
                                           milestone_id=milestone.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        tasks_titles = [ task["title"] for task in data ]
        self.assertIn("First Task", tasks_titles)
        self.assertIn("Second Task", tasks_titles)

    def test_for_presence_of_uri_to_tasks(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        task = milestone.add_task(title="First Task", 
                                  deadline=datetime(2017, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.milestone_tasks", 
                                           username="Test",
                                           project_id=project.id, 
                                           milestone_id=milestone.id))   
        data = response.json
        self.assertIn(url_for("api.milestone_task_get", username="Test",
                              project_id=project.id, milestone_id=milestone.id,
                              task_id=task.id), 
                      data[0]["uri"])

    def test_for_creating_new_task_with_post_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        self.login(name="Test")
        response = self.client.post(url_for("api.milestone_task_create", 
                                            username="Test", 
                                            project_id=project.id, 
                                            milestone_id=milestone.id),  
                                    data=dict(title="First Task", 
                                              deadline="2017-01-01 00:00"))
        self.assertEqual(response.status_code, 201)
        task = user.projects[0].milestones[0].tasks[0]
        self.assertEqual(task.milestone.project, project)
        self.assertEqual(task.title, "First Task")

    def test_for_returning_Bad_Request_when_no_task_title(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        self.login(name="Test")
        response = self.client.post(url_for("api.milestone_task_create", 
                                            username="Test", 
                                            project_id=project.id, 
                                            milestone_id=milestone.id),  
                                    data=dict(name="First Task", 
                                              deadline="2017-01-01 00:00"))
        self.assertEqual(response.status_code, 400)

    def test_for_returning_Bad_Request_when_no_task_deadline(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        self.login(name="Test")
        response = self.client.post(url_for("api.milestone_task_create", 
                                            username="Test", 
                                            project_id=project.id, 
                                            milestone_id=milestone.id),  
                                    data=dict(title="First Task", 
                                              deathline="2017-01-01 00:00"))
        self.assertEqual(response.status_code, 400)

    def test_post_request_returns_URI_to_new_task(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        milestone = project.add_milestone(title="First Milestone")
        self.login(name="Test")
        response = self.client.post(url_for("api.milestone_tasks", 
                                            username="Test", 
                                            project_id=project.id, 
                                            milestone_id=milestone.id),  
                                    data=dict(title="First Task", 
                                              deadline="2017-01-01 00:00"))
        self.assertEqual(response.status_code, 201)
        task = milestone.tasks[0]
        self.assertIn(url_for("api.milestone_task_get", username="Test", 
                              task_id=task.id, project_id=project.id, 
                              milestone_id=milestone.id),
                      response.location)


class TestApiProjectMilestoneTaskItem(ApiTestCase):

    def test_get_request_returns_information_about_task(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        milestone = project.add_milestone(title="Milestone 1")
        task = milestone.add_task(title="Task 1", 
                                  deadline=datetime(2017, 12, 31, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.milestone_task_get", 
                                           username="Test",
                                           project_id=project.id, 
                                           milestone_id=milestone.id,
                                           task_id=task.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["title"], task.title)
        self.assertEqual(data["deadline"], "2017-12-31 00:00")

    def test_get_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        milestone = project.add_milestone(title="Milestone 1")
        task = milestone.add_task(title="Task 1", 
                                  deadline=datetime(2017, 6, 12, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.milestone_task_get", 
                                           username="Test", 
                                           project_id=project.id, 
                                           milestone_id=milestone.id, 
                                           task_id=task.id+1))
        self.assertEqual(response.status_code, 404)

    def test_for_updating_task_with_put_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        milestone = project.add_milestone(title="Milestone 1")
        task = milestone.add_task(title="My First Task", 
                                  deadline=datetime(2017, 1, 1, 0, 0))
        self.login(name="Test") 
        response = self.client.put(url_for("api.milestone_task_edit", 
                                           username="Test", 
                                           project_id=project.id, 
                                           milestone_id=milestone.id,
                                           task_id=task.id),
                                   data=dict(title="My Last Task", 
                                             complete="YES"))
        task = db.session.query(User).one().projects[0].milestones[0].tasks[0]
        self.assertEqual(response.status_code, 204)
        self.assertEqual(task.title, "My Last Task")
        self.assertEqual(task.complete, True)

    def test_put_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        milestone = project.add_milestone(title="Milestone 1")
        task = milestone.add_task(title="My First Task", 
                                  deadline=datetime(2017, 1, 1, 0, 0))
        self.login(name="Test") 
        response = self.client.put(url_for("api.milestone_task_edit", 
                                           username="Test", 
                                           project_id=project.id, 
                                           milestone_id=milestone.id,
                                           task_id=task.id+1))
        self.assertEqual(response.status_code, 404)

    def test_for_deleting_task_with_delete_request(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        milestone = project.add_milestone(title="Milestone 1")
        task = milestone.add_task(title="Last but one task", 
                                  deadline=datetime(9999, 12, 31, 23, 59))
        self.login(name="Test")
        response = self.client.delete(url_for("api.milestone_task_delete", 
                                              username="Test",
                                              project_id=project.id, 
                                              milestone_id=milestone.id,
                                              task_id=task.id))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(milestone.tasks), 0)
        self.assertEqual(db.session.query(Task).count(), 0)

    def test_delete_request_returns_Not_Found_for_unknwon_id(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Project 1", 
                                   deadline=datetime(2017, 1, 1, 0, 0))
        milestone = project.add_milestone(title="Milestone 1")
        task = milestone.add_task(title="Last but one task", 
                                  deadline=datetime(9999, 12, 31, 23, 59))
        self.login(name="Test")
        response = self.client.delete(url_for("api.milestone_task_delete", 
                                              username="Test",
                                              project_id=project.id, 
                                              milestone_id=milestone.id,
                                              task_id=task.id+1))
        self.assertEqual(response.status_code, 404)


class TestApiTagsList(ApiTestCase):

    def test_get_request_returns_lists_of_available_tags(self):
        user = self.create_user(name="Test")
        tag1 = Tag.find_or_create(name="Test")
        tag2 = Tag.find_or_create(name="Winter")
        self.login(name="Test")
        response = self.client.get(url_for("api.tags"))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        self.assertEqual(set(tag["name"] for tag in data), 
                         {"Test", "Winter"})

    def test_put_request_creates_new_tag(self):
        self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.put(url_for("api.tag_create",  
                                           name="Test"))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(db.session.query(Tag).count(), 1)
        self.assertEqual(db.session.query(Tag).one().name, "Test")
    
    def test_put_request_does_not_create_tag_if_exists(self):
        self.create_user(name="Test")
        Tag.find_or_create(name="Tag")
        self.login(name="Test")
        response = self.client.put(url_for("api.tag_create", 
                                           name="Tag"))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(db.session.query(Tag).count(), 1)

class TestApiTagItem(ApiTestCase):

    def test_get_request_returns_204_when_tag_exists(self):
        self.create_user(name="Test")
        tag = Tag.find_or_create("Tag")
        self.login(name="Test")
        response = self.client.get(url_for("api.tag_get", name="Tag"))
        self.assertEqual(response.status_code, 204)

    def test_get_request_returns_404_when_tag_does_not_exist(self):
        self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.get(url_for("api.tag_get", name="Tag"))
        self.assertEqual(response.status_code, 404)

    def test_for_deleting_tag_with_delete_request(self):
        self.create_user(name="Test")
        Tag.find_or_create("Tag")
        self.login(name="Test")
        response = self.client.delete(url_for("api.tag_delete", name="Tag"))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(db.session.query(Tag).count(), 0)

    def test_delete_requests_returns_404_when_no_tag_with_given_name(self):
        self.create_user(name="Test")
        Tag.find_or_create("Tag")
        self.login(name="Test")
        response = self.client.delete(url_for("api.tag_delete", name="Tagr"))
        self.assertEqual(response.status_code, 404)     
        self.assertEqual(db.session.query(Tag).count(), 1)
     

class TestEventsList(ApiTestCase):

    def test_get_request_returns_list_of_events(self):
        user = self.create_user(name="Test")
        event1 = user.add_event(title="My First Event", 
                                start=datetime(2017, 1, 1, 0, 0),
                                end=datetime(2017, 1, 1, 0, 0))
        event2 = user.add_event(title="My Second Event",
                                start=datetime(2017, 1, 1, 0, 0),
                                end=datetime(2017, 1, 1, 12, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.events", 
                                   username=user.username))
        data = response.json
        self.assertEqual(len(data), 2)
        events_titles = [ event["title"] for event in data ]
        self.assertIn(event1.title, events_titles)
        self.assertIn(event2.title, events_titles)

    def test_get_request_accepts_date_range_in_query(self):
        user = self.create_user(name="Test")
        event1 = user.add_event(title="My Second Event", 
                                start=datetime(2017, 1, 1, 0, 0),
                                end=datetime(2017, 1, 1, 0, 0))
        event2 = user.add_event(title="My First Event",
                                start=datetime(2019, 1, 1, 0, 0),
                                end=datetime(2019, 1, 1, 12, 0))
                                
        self.login(name="Test")
        response = self.client.get(url_for("api.events", username=user.username),
                                   data=dict(start="2017-01-01",
                                             end="2018-01-01"))
        data = response.json
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "My Second Event")


    def test_for_presence_of_uri_to_tasks(self):
        user = self.create_user(name="Test")
        event = user.add_event(title="My First Event", 
                                start=datetime(2017, 1, 1, 0, 0),
                                end=datetime(2017, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.events", username="Test"))   
        data = response.json
        self.assertIn(url_for("api.event_get", username="Test",
                              event_id=event.id), 
                      data[0]["uri"])

    def test_post_request_creates_new_event(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.event_create", username="Test"),
                                    data=dict(title="My First Event",
                                              start="2017-01-01 12:00",
                                              end="2017-01-01 15:00"))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(db.session.query(Event).count(), 1)
        self.assertEqual(user.events.count(), 1)
        event = db.session.query(Event).one()
        self.assertEqual(event.title, "My First Event")
        self.assertEqual(event.end, datetime(2017, 1, 1, 15, 0))

    def test_post_request_returns_uri_to_new_event(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.event_create", username="Test"),
                                    data=dict(title="My First Event",
                                              start="2017-01-01 12:00",
                                              end="2017-01-01 15:00"))
        self.assertEqual(response.status_code, 201)
        event = user.events.one()
        self.assertIn(url_for("api.event_get", username="Test", 
                                 event_id=event.id),
                         response.location)        

    def test_event_create_returns_Bad_Request_when_no_title(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.event_create", username="Test"),
                                    data=dict(name="My First Event",
                                              start="2017-01-01 12:00",
                                              end="2017-01-01 15:00"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(db.session.query(Event).count(), 0)

    def test_event_create_returns_Bad_Request_when_no_start_date(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.event_create", username="Test"),
                                    data=dict(title="My First Event",
                                              begin="2017-01-01 12:00",
                                              end="2017-01-01 15:00"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(db.session.query(Event).count(), 0)

    def test_event_create_returns_Bad_Request_when_invalid_format_of_dates(self):
        user = self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.post(url_for("api.event_create", username="Test"),
                                    data=dict(title="My First Event",
                                              start="2017-01-01",
                                              end="07-01-1900 15:00"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(db.session.query(Event).count(), 0)        


class TestEventItem(ApiTestCase):

    def test_get_request_returns_information_about_event(self):
        user = self.create_user(name="Test")
        event = user.add_event(title="First Task", 
                               start=datetime(2015, 1, 1, 0, 0),
                               end=datetime(2016, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.event_get", username="Test",
                                           event_id=event.id))
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["title"], event.title)
        self.assertEqual(data["start"], "2015-01-01 00:00")
        self.assertEqual(data["end"], "2016-01-01 00:00")

    def test_get_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        event = user.add_event(title="First Task", 
                               start=datetime(2015, 1, 1, 0, 0),
                               end=datetime(2016, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.get(url_for("api.event_get", username="Test", 
                                           event_id=event.id+1))
        self.assertEqual(response.status_code, 404)

    def test_for_updating_event_with_put_request(self):
        user = self.create_user(name="Test")
        event = user.add_event(title="First Task", 
                               start=datetime(2015, 1, 1, 0, 0),
                               end=datetime(2016, 1, 1, 0, 0))
        self.login(name="Test") 
        response = self.client.put(url_for("api.event_edit", username="Test", 
                                           event_id=event.id),
                                   data=dict(title="New Title", 
                                             end="2017-01-01 00:00"))
        self.assertEqual(response.status_code, 204)
        event = db.session.query(User).one().events[0]
        self.assertEqual(event.title, "New Title")
        self.assertEqual(event.end, datetime(2017, 1, 1, 0, 0))

    def test_put_request_returns_Not_Found_for_unknown_id(self):
        user = self.create_user(name="Test")
        event = user.add_event(title="First Task", 
                               start=datetime(2015, 1, 1, 0, 0),
                               end=datetime(2016, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.put(url_for("api.event_edit", username="Test", 
                                           event_id=event.id+1),
                                   data=dict(title="New Title"))
        self.assertEqual(response.status_code, 404)

    def test_put_request_returns_Bad_Request_when_invalid_data(self):
        user = self.create_user(name="Test")
        event = user.add_event(title="First Task", 
                               start=datetime(2015, 1, 1, 0, 0),
                               end=datetime(2016, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.put(url_for("api.event_edit", username="Test", 
                                           event_id=event.id),
                                   data=dict(title="New Title",
                                             start="2017-13-34 00:00",
                                             end="12-01-2019"))
        self.assertEqual(response.status_code, 400)

    def test_for_deleting_event_with_delete_request(self):
        user = self.create_user(name="Test")
        event = user.add_event(title="First Task", 
                               start=datetime(2015, 1, 1, 0, 0),
                               end=datetime(2016, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.delete(url_for("api.event_delete", username="Test",
                                              event_id=event.id))
        self.assertEqual(response.status_code, 204) # 204 - NO CONTENT
        self.assertEqual(user.events.count(), 0)
        self.assertEqual(db.session.query(Event).count(), 0)

    def test_delete_request_returns_Not_Found_for_unknwon_id(self):
        user = self.create_user(name="Test")
        event = user.add_event(title="First Task", 
                               start=datetime(2015, 1, 1, 0, 0),
                               end=datetime(2016, 1, 1, 0, 0))
        self.login(name="Test")
        response = self.client.delete(url_for("api.event_delete", username="Test",
                                              event_id=event.id+1))
        self.assertEqual(response.status_code, 404)