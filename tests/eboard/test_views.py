import sys
import unittest
from datetime import datetime

from flask_testing import TestCase #http://pythonhosted.org/Flask-Testing/
from flask import url_for

from app import create_app, db
from app.models import User, Task


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

    def login(self, username="Test", password="test"):
        return self.client.post(url_for("auth.login"), data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get(url_for("auth.logout"), follow_redirects=True)


class TestUser(EboardTestCase):

    def test_uses_proper_template_used(self):
        self.create_user()
        self.login()
        self.client.get(url_for("eboard.user_index", username="Test"))
        self.assert_template_used("eboard/index.html")

    def test_returns_not_found_when_no_user(self):
        user = self.create_user()
        self.login()
        response = self.client.get(url_for("eboard.user_index", 
                                           username="Empty"))
        self.assert_404(response)

    def test_returns_not_found_when_private_profile(self):
        self.create_user()
        user = self.create_user(username="Nowy")
        self.login(username="Nowy")
        response = self.client.get(url_for("eboard.user_index", 
                                           username="Test"))
        self.assert_404(response)

    def test_returns_ok_when_public_profile(self):
        user = self.create_user(username="Test")
        user.public = True
        db.session.commit()
        user = self.create_user(username="Nowy")
        self.login(username="Nowy")
        response = self.client.get(url_for("eboard.user_index", 
                                           username="Test"))
        self.assert_200(response) 

    @unittest.skip #login_required turn off in config
    def test_redirects_anonymous_user_to_login_page(self):
        self.create_user()
        response = self.client.get(url_for("eboard.user_index", 
                                           username="Test"),
                                   follow_redirects=False)
        self.assertRedirects(response, url_for("eboard.index"))


class TestTasks(EboardTestCase):

    def test_uses_proper_template_for_get_request(self):
        self.create_user(username="Test")
        self.login(username="Test")
        self.client.get(url_for("eboard.user_tasks", username="Test"),
                        data=dict(page=1))
        self.assert_template_used("eboard/tasks.html")

    def test_passes_pagination_and_tasks_to_template(self):
        user = self.create_user(username="Test")
        user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.login(username="Test")
        self.client.get(url_for("eboard.user_tasks", username="Test"),
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
        self.client.get(url_for("eboard.user_tasks", username="Test"),
                        data=dict(page=1))
        tasks = self.get_context_variable("tasks")
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[1].title, "Test Task")

    def test_creates_new_task_with_post_request(self):
        user = self.create_user(username="Test")
        self.login(username="Test")
        self.client.post(url_for("eboard.user_tasks_create", username="Test"), 
                         data=dict(title="Test Task", 
                                   deadline="2015-01-01 00:00:00"),
                         follow_redirects=True)
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(user.tasks.count(), 1)
        task = user.tasks.one()
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.deadline, datetime(2015, 1, 1, 0, 0))