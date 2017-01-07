import sys

from flask_testing import TestCase #http://pythonhosted.org/Flask-Testing/

from app import create_app, db
from app.models import User, Task


class TestUser(TestCase):

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_user(self):
        user = User(username="Test", password="test")
        db.session.add(user)
        db.session.commit()
        return user

    def test_creates_user_with_no_tasks(self):
        user = self.create_user()
        self.assertEqual(user.tasks.count(), 0)

    def test_creates_private_profile_by_default(self):
        user = User(username="Test", password="test")
        db.session.add(user)
        db.session.commit()
        self.assertEqual(user.public, False)

    def test_adds_task_for_user(self):
        user = self.create_user()
        user.add_task(title="Test Task")
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(user.tasks[0], Task.query.one())
        self.assertEqual(db.session.query(Task).one().user, user)

    def test_passes_args_to_add_task(self):
        user = self.create_user()
        user.add_task(title="Test Task", importance=3)
        task = user.tasks[0]
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.importance, 3)

    def test_add_task_returns_task(self):
        user = self.create_user()
        task = user.add_task(title="Test Task")
        self.assertEqual(task, db.session.query(Task).one())

    def test_for_preventing_commit_when_adding_task(self):
        user = self.create_user()
        user.add_task(title="Test Task", commit=False)
        db.session.rollback() 
        self.assertEqual(db.session.query(Task).count(), 0)
        self.assertEqual(user.tasks.count(), 0)

    def test_for_commiting_when_adding_task(self):
        user = self.create_user()
        user.add_task(title="Test Task")
        db.session.rollback()
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(db.session.query(Task).one().user, user)

    def test_add_task_accepts_task_object_as_first_argument(self):
        user = self.create_user()
        task = Task(title="FUCK")
        db.session.add(task)
        db.session.commit()
        user.add_task(task)
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(user.tasks.count(), 1)
        self.assertEqual(user.tasks[0], task)

    def test_remove_task_by_id_from_user_tasks_list(self):
        user = self.create_user()
        task = user.add_task(title="Task to remove")
        self.assertEqual(user.tasks.count(), 1)
        user.remove_task(task.id)
        self.assertEqual(user.tasks.count(), 0)

    def test_remove_task_by_object_from_user_tasks_list(self):
        user = self.create_user()
        task = user.add_task(title="Task to remove")
        self.assertEqual(user.tasks.count(), 1)
        user.remove_task(task)
        self.assertEqual(user.tasks.count(), 0)

    def test_remove_task_does_not_raise_exception_when_invalid_id(self):
        user = self.create_user()
        task = user.add_task(title="Task to remove")
        self.assertEqual(user.tasks.count(), 1)
        user.remove_task(345)
        self.assertEqual(user.tasks.count(), 1)

        