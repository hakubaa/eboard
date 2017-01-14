import sys
import unittest
from datetime import datetime

from flask_testing import TestCase #http://pythonhosted.org/Flask-Testing/
from flask import url_for

from app import create_app, db
from app.models import User, Task, Project
from app.eboard.forms import TaskForm, ProjectForm


class EboardTestCase(TestCase):

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_user(self, username="Test", password="test"):
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, username="Test", password="test", follow_redirects=True):
        return self.client.post(url_for("auth.login"), data=dict(
            username=username,
            password=password
        ), follow_redirects=follow_redirects)

    def logout(self):
        return self.client.get(url_for("auth.logout"), follow_redirects=True)


class TestUser(EboardTestCase):

    def test_uses_proper_template_used(self):
        self.create_user()
        self.login()
        self.client.get(url_for("eboard.index", username="Test"))
        self.assert_template_used("eboard/index.html")

    def test_returns_not_found_when_no_user(self):
        user = self.create_user()
        self.login()
        response = self.client.get(url_for("eboard.index", 
                                           username="Empty"))
        self.assert_404(response)

    def test_returns_not_found_when_private_profile(self):
        self.create_user()
        user = self.create_user(username="Nowy")
        self.login(username="Nowy")
        response = self.client.get(url_for("eboard.index", 
                                           username="Test"))
        self.assert_404(response)

    def test_returns_ok_when_public_profile(self):
        user = self.create_user(username="Test")
        user.public = True
        db.session.commit()
        user = self.create_user(username="Nowy")
        self.login(username="Nowy")
        response = self.client.get(url_for("eboard.index", 
                                           username="Test"))
        self.assert_200(response) 

    @unittest.skip #login_required turn off in config
    def test_redirects_anonymous_user_to_login_page(self):
        self.create_user()
        response = self.client.get(url_for("eboard.index", 
                                           username="Test"),
                                   follow_redirects=False)
        self.assertRedirects(response, url_for("eboard.index"))


class TestTasks(EboardTestCase):

    def test_uses_proper_template_for_get_request(self):
        self.create_user(username="Test")
        self.login(username="Test")
        self.client.get(url_for("eboard.tasks", username="Test"),
                        data=dict(page=1))
        self.assert_template_used("eboard/tasks.html")

    def test_passes_pagination_and_tasks_to_template(self):
        user = self.create_user(username="Test")
        user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.get(url_for("eboard.tasks", username="Test"),
                        data=dict(page=1))
        pagination = self.get_context_variable("pagination")
        tasks = self.get_context_variable("tasks")
        self.assertTrue(pagination)
        self.assertTrue(tasks)
        self.assertEqual(pagination.page, 1)
        self.assertEqual(tasks[0].title, "Test Task")

    def test_renders_tasks_of_the_proper_user(self):
        user = self.create_user(username="Test")
        user.public = True
        user.add_task(title="Test Task", deadline=datetime(2018, 1, 1, 0, 0))
        user.add_task(title="Next Task", deadline=datetime(2019, 1, 1, 0, 0))
        user = self.create_user(username="Nowy")
        user.add_task(title="Nowy Task", deadline=datetime(2016, 1, 1, 0, 0))
        self.login(username="Nowy")
        self.client.get(url_for("eboard.tasks", username="Test"),
                        data=dict(page=1))
        tasks = self.get_context_variable("tasks")
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[1].title, "Test Task")


class TestNewTask(EboardTestCase):

    def test_uses_proper_template(self):
        self.create_user(username="Test")
        self.login(username="Test")
        self.client.get(url_for("eboard.task_create", username="Test"))
        self.assert_template_used("eboard/task_edit.html")

    def test_passess_form_to_template(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        self.client.get(url_for("eboard.task_create", username="Test"))   
        form = self.get_context_variable("form")
        self.assertIsInstance(form, TaskForm)

    def test_creates_new_task_with_post_request(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        self.client.post(url_for("eboard.task_create", username="Test"), 
                         data=dict(title="Test Task", 
                                   deadline="2015-01-01 00:00"),
                         follow_redirects=True)
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(user.tasks.count(), 1)
        task = user.tasks.one()
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.deadline, datetime(2015, 1, 1, 0, 0))

    def test_redirects_to_tasks_page_when_success(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        response = self.client.post(url_for("eboard.task_create", username="Test"), 
                         data=dict(title="Test Task", 
                                   deadline="2015-01-01 00:00"),
                         follow_redirects=False)
        self.assertRedirects(response, url_for("eboard.tasks", username="Test"))

    def test_shows_msg_when_no_deadline(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        response = self.client.post(url_for("eboard.task_create", username="Test"), 
                         data=dict(title="Test Task"),
                         follow_redirects=False)
        self.assertNotEqual(response.data.find(b"This field is required."), -1)

    def test_shows_msg_when_no_title(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        response = self.client.post(url_for("eboard.task_create", username="Test"), 
                         data=dict(deadline="2015-01-01 00:00"),
                         follow_redirects=False)
        self.assertNotEqual(response.data.find(b"This field is required."), -1)


class TestShowTask(EboardTestCase):

    def test_uses_proper_template(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.get(url_for("eboard.task_show", username="Test", 
                        task_id=task.id))
        self.assert_template_used("eboard/task.html")

    def test_passess_task_to_template(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.get(url_for("eboard.task_show", username="Test", 
                                task_id=task.id))   
        task_test = self.get_context_variable("task")
        self.assertIsInstance(task_test, Task)
        self.assertEqual(task_test, task)

    def test_returns_not_found_when_task_does_not_exist(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.get(url_for("eboard.task_show", username="Test", 
                                           task_id=task.id+1))   
        self.assert_404(response)


class TestEditTask(EboardTestCase):

    def test_uses_proper_template(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.get(url_for("eboard.task_edit", username="Test",
                                task_id=task.id))
        self.assert_template_used("eboard/task_edit.html")

    def test_returns_not_found_when_task_does_not_exist(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.get(url_for("eboard.task_edit", username="Test",
                                           task_id=task.id+1))
        self.assert_404(response)

    def test_for_populating_form_with_task_data(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Task To Populate", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.get(url_for("eboard.task_edit", username="Test",
                                           task_id=task.id))
        self.assertNotEqual(response.data.find(b"Task To Populate"), -1)    

    def test_update_task_with_post_request(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.post(url_for("eboard.task_edit", username="Test", 
                                 task_id=task.id), 
                         data=dict(title="New Task Title", 
                                   deadline="2018-01-01 00:00"),
                         follow_redirects=True)
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(user.tasks.count(), 1)
        task = user.tasks.one()
        self.assertEqual(task.title, "New Task Title")
        self.assertEqual(task.deadline, datetime(2018, 1, 1, 0, 0))

    def test_redirects_to_tasks_page_when_success(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.post(url_for("eboard.task_edit", username="Test", 
                                            task_id=task.id), 
                                    data=dict(title="New Task Title", 
                                              deadline="2018-01-01 00:00"),
                                    follow_redirects=False)
        self.assertRedirects(response, url_for("eboard.tasks", username="Test"))


class TestDeleteTask(EboardTestCase):

    def test_for_delating_task(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test Task",
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.delete(url_for("eboard.task_delete",
                                              username="Test", task_id=task.id),
                                      follow_redirects=False)
        self.assertEqual(db.session.query(Task).count(), 0)
        self.assertEqual(user.tasks.count(), 0)

    def test_redirects_to_tasks_page_when_success(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test Task",
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.delete(url_for("eboard.task_delete",
                                              username="Test", task_id=task.id),
                                      follow_redirects=False)
        self.assertRedirects(response, url_for("eboard.tasks", username="Test"))


    def test_returns_not_found_when_task_does_not_exist(self):
        user = self.create_user(username="Test")
        task = user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.delete(url_for("eboard.task_delete",
                                              username="Test", task_id=task.id+1),
                                      follow_redirects=False)
        self.assert_404(response)


class TestProjects(EboardTestCase):

    def test_uses_proper_template_to_show_projects(self):
        self.create_user(username="Test")
        self.login(username="Test", follow_redirects=False)
        self.client.get(url_for("eboard.projects", username="Test"),
                        data=dict(page=1))
        self.assert_template_used("eboard/projects.html")

    def test_passes_pagination_and_projects_to_template(self):
        user = self.create_user(username="Test")
        user.add_project(name="First Project", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test", follow_redirects=False)
        self.client.get(url_for("eboard.projects", username="Test"),
                        data=dict(page=1))
        pagination = self.get_context_variable("pagination")
        projects = self.get_context_variable("projects")
        self.assertTrue(pagination)
        self.assertTrue(projects)
        self.assertEqual(pagination.page, 1)
        self.assertEqual(projects[0].name, "First Project")

    def test_renders_projects_of_the_proper_user(self):
        user = self.create_user(username="Test")
        user.public = True
        user.add_project(name="Test Project", deadline=datetime(2018, 1, 1, 0, 0))
        user.add_project(name="Next Project", deadline=datetime(2019, 1, 1, 0, 0))
        user = self.create_user(username="Nowy")
        user.add_project(name="New Project", deadline=datetime(2016, 1, 1, 0, 0))
        self.login(username="Nowy", follow_redirects=False)
        self.client.get(url_for("eboard.projects", username="Test"),
                        data=dict(page=1))
        projects = self.get_context_variable("projects")
        self.assertEqual(len(projects), 2)
        projects_names = [ project.name for project in projects ]
        self.assertIn("Next Project", projects_names)


class TestProjectNew(EboardTestCase):

    def test_renders_proper_template(self):
        self.create_user(username="Test")
        self.login(username="Test", follow_redirects=False)
        response = self.client.get(url_for("eboard.project_create", username="Test"))
        self.assert_template_used("eboard/project_edit.html")

    def test_passess_proper_form_to_template(self):
        self.create_user(username="Test")
        self.login(username="Test")
        response = self.client.get(url_for("eboard.project_create", 
                                           username="Test"))
        form = self.get_context_variable("form")
        self.assertIsInstance(form, ProjectForm)

    def test_creates_new_project_with_post_request(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        response = self.client.post(url_for("eboard.project_create",
                                            username="Test"),
                                    data=dict(name="My First Project",
                                              deadline="2017-01-01 00:00"))
        self.assertEqual(db.session.query(Project).count(), 1)
        self.assertEqual(user.projects.count(), 1)

    def test_creates_new_project_in_accordance_with_user_data(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        response = self.client.post(url_for("eboard.project_create",
                                            username="Test"),
                                    data=dict(name="My First Project",
                                              deadline="2017-01-01 00:00",
                                              desc="Improve your memory."))
        project = user.projects[0]
        self.assertEqual(project.name, "My First Project")
        self.assertEqual(project.deadline, datetime(2017, 1, 1, 0, 0))
        self.assertEqual(project.desc, "Improve your memory.")

    def test_redirects_to_page_with_projects_when_success(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        response = self.client.post(url_for("eboard.project_create",
                                            username="Test"),
                                    data=dict(name="My First Project",
                                              deadline="2017-01-01 00:00"))
        self.assertRedirects(response, url_for("eboard.projects", 
                                               username="Test"))

    def test_shows_msg_when_no_deadline(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        response = self.client.post(url_for("eboard.project_create", 
                                            username="Test"), 
                         data=dict(name="Test Project"),
                         follow_redirects=False)
        self.assertNotEqual(response.data.find(b"This field is required."), -1)

    def test_shows_msg_when_no_project_name(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        response = self.client.post(url_for("eboard.project_create", 
                                            username="Test"), 
                         data=dict(deadline="2015-01-01 00:00"),
                         follow_redirects=False)
        self.assertNotEqual(response.data.find(b"This field is required."), -1)


class TestShowProject(EboardTestCase):

    def test_uses_proper_template(self):
        user = self.create_user(username="Test")
        project = user.add_project(name="Test Project", 
                                deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.get(url_for("eboard.project_show", username="Test", 
                        project_id=project.id))
        self.assert_template_used("eboard/project.html")

    def test_passess_project_to_template(self):
        user = self.create_user(username="Test")
        project = user.add_project(name="Test Project", 
                                deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.get(url_for("eboard.project_show", username="Test", 
                                project_id=project.id))   
        project_test = self.get_context_variable("project")
        self.assertIsInstance(project_test, Project)
        self.assertEqual(project_test, project)

    def test_returns_not_found_when_project_does_not_exist(self):
        user = self.create_user(username="Test")
        project = user.add_project(name="Test Task", 
                                deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.get(url_for("eboard.project_show", 
                                           username="Test", 
                                           project_id=project.id+1))   
        self.assert_404(response)


class TestEditProject(EboardTestCase):

    def test_uses_proper_template(self):
        user = self.create_user(username="Test")
        project = user.add_project(name="Test Project",  
                                deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.get(url_for("eboard.project_edit", username="Test",
                                project_id=project.id))
        self.assert_template_used("eboard/project_edit.html")

    def test_returns_not_found_when_project_does_not_exist(self):
        user = self.create_user(username="Test")
        project = user.add_project(name="Test Project", 
                                deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.get(url_for("eboard.project_edit", 
                                           username="Test",
                                           project_id=project.id+1))
        self.assert_404(response)

    def test_for_populating_form_with_project_data(self):
        user = self.create_user(username="Test")
        project = user.add_project(name="Project To Populate", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.get(url_for("eboard.project_edit", 
                                           username="Test",
                                           project_id=project.id))
        self.assertNotEqual(response.data.find(b"Project To Populate"), -1)    

    def test_update_project_with_post_request(self):
        user = self.create_user(username="Test")
        project = user.add_project(name="Test Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.post(url_for("eboard.project_edit", username="Test", 
                                 project_id=project.id), 
                         data=dict(name="New Project Title", 
                                   deadline="2018-01-01 00:00"),
                         follow_redirects=True)
        self.assertEqual(db.session.query(Project).count(), 1)
        self.assertEqual(user.projects.count(), 1)
        project = user.projects.one()
        self.assertEqual(project.name, "New Project Title")
        self.assertEqual(project.deadline, datetime(2018, 1, 1, 0, 0))

    def test_redirects_to_projects_page_when_success(self):
        user = self.create_user(username="Test")
        project = user.add_project(name="Test Project", 
                                deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        response = self.client.post(url_for("eboard.project_edit", 
                                            username="Test", 
                                            project_id=project.id), 
                                    data=dict(name="New Project Title", 
                                              deadline="2018-01-01 00:00"),
                                    follow_redirects=False)
        self.assertRedirects(response, url_for("eboard.projects", 
                                               username="Test"))