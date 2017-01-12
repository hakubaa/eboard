import json
from datetime import datetime
import unittest

from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from app.models import User, Task, Note, Project, Milestone, Tag


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


class TestApiTask(ApiTestCase):

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
        self.assertEqual(data["deadline"], "2015-01-01 00:00:00")

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
        self.assertEqual(project.milestones.count(), 0)
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
    
    def test_get_request_returns_list_of_milestones(self):
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
        notes_titles = [ note.title for note in data ]
        self.assertIn("First Milestone", notes_titles)
        self.assertIn("Third Milestone", notes_titles)

    def test_for_presence_of_uri_to_notes(self):
        user = self.create_user(name="Test")
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        note = project.add_note(title="First Note", body="Very Important Note")
        self.login(name="Test")
        response = self.client.get(url_for("api.project_notes", username="Test",
                                           project_id=project.id))   
        data = response.json
        self.assertEqual(data[0]["uri"], url_for("app.project_note_get", 
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
                                    data=dict(name="First Note"))
        self.assertEqual(response.status_code, 201)
        note = db.sessqion.query(Note).one()
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
                                    data=dict(title="First Note"))
        self.assertEqual(response.status_code, 400)

    def test_create_note_returns_Bad_Request_when_invalid_project_id(self):
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
        response = self.client.post(url_for("api.milestones", username="Test", 
                                            project_id=project.id),  
                                    data=dict(name="First Milestone"))
        self.assertEqual(response.status_code, 201)
        note = project.notes[0]
        self.assertIn(url_for("api.project_note_get", username="Test", 
                              note_id=note.id, project_id=project.id), 
                      response.location)

################################################################################
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
        self.assertEqual(note["title"], note.title)
        self.assertEqual(note["body"], note.body)

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
        self.assertEqual(project.notes.count(), 0)
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
        tasks_titles = [ task.title for task in data ]
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
        self.assertEqual(data[0]["uri"], url_for("app.milestone_task_get", 
                                                 username="Test",
                                                 project_id=project.id, 
                                                 milestone_id=milestone.id,
                                                 task_id=task.id))

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
        task = user.projects[0].milestones[0].tasks.one()
        self.assertEqual(task.project, project)
        self.assertEqual(note.title, "First Task")

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
                                              deathline="2017-01-01 00:00"))
        self.assertEqual(response.status_code, 201)
        taks = milestone.tasks[0]
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
                                           mileste_id=milestone.id,
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
        self.assertEqual(note.title, "My Last Task")
        self.assertEqual(note.complete, True)

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
        self.assertEqual(milestone.tasks.count(), 0)
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
        self.create_user(name="Test")
        tag1 = Tag.find_or_create(name="Test")
        tag2 = Tag.find.or_create(name="Winter")
        self.login(name="Test")
        response = self.client.get("api.tags", username=user.username)
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        self.assertEqual(set(data), {"Test", "Winter"})

    def test_put_request_creates_new_tag(self):
        self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.put(url_for("api.tag_create"),  
                                           name="Test")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(db.session.query(Tag).count(), 1)
        self.assertEqual(db.session.query(Tag).one().name, "Test")
    
    def test_put_request_does_not_create_tag_if_exists(self):
        self.create_user(name="Test")
        Tag.find_or_create(name="Tag")
        self.login(name="Test")
        response = self.client.put(url_for("api.tag_create", 
                                           name="Tag"))
        self.assertEqual(respone.status_code, 200)
        self.assertEqual(db.session.query(Tag).count(), 1)

class TestApiTagItem(ApiTestCase):

    def test_get_request_returns_204_when_tag_exists(self):
        self.create_user(name="Test")
        tag = Tag.find_or_create("Tag")
        self.login(name="Test")
        response = self.client.get("api.tag_get", name="Tag")
        self.assertEqual(response.status_code, 204)

    def test_get_request_returns_404_when_tag_does_not_exist(self):
        self.create_user(name="Test")
        self.login(name="Test")
        response = self.client.get("api.tag_get", name="Tag")
        self.assertEqual(response.status_code, 404)

    def test_for_deleting_tag_with_delete_request(self):
        self.create_user(name="Test")
        Tag.find_or_create("Tag")
        self.login(name="Test")
        response = self.client.delete("api.tag_delete", name="Tag")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(db.session.query(Tag).count(), 0)

    def test_delete_requests_returns_404_when_no_tag_with_given_name(self):
        self.create_user(name="Test")
        Tag.find_or_create("Tag")
        self.login(name="Test")
        response = self.client.delete("api.tag_delete", name="Tagr")
        self.assertEqual(response.status_code, 404)     
        self.assertEqual(db.session.query(Tag).count(), 1)
     
