import sys
from datetime import datetime, timedelta
import unittest

from flask_testing import TestCase #http://pythonhosted.org/Flask-Testing/

from app import create_app, db
from app.models import User, Task, Event, Project


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

    def test_add_task_creates_new_task_for_user(self):
        user = self.create_user()
        user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(user.tasks[0], Task.query.one())
        self.assertEqual(db.session.query(Task).one().user, user)

    def test_passes_args_to_add_task(self):
        user = self.create_user()
        user.add_task(title="Test Task", importance=3, 
                      deadline=datetime(2015, 1, 1, 0, 0))
        task = user.tasks[0]
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.importance, 3)

    def test_add_task_returns_task(self):
        user = self.create_user()
        task = user.add_task(title="Test Task", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(task, db.session.query(Task).one())

    def test_for_preventing_commit_when_adding_task(self):
        user = self.create_user()
        user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0), 
                      commit=False)
        db.session.rollback() 
        self.assertEqual(db.session.query(Task).count(), 0)
        self.assertEqual(user.tasks.count(), 0)

    def test_for_commiting_when_adding_task(self):
        user = self.create_user()
        user.add_task(title="Test Task", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.rollback()
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(db.session.query(Task).one().user, user)

    def test_add_task_accepts_task_object_as_first_argument(self):
        user = self.create_user()
        task = Task(title="FUCK", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()
        user.add_task(task)
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(user.tasks.count(), 1)
        self.assertEqual(user.tasks[0], task)

    def test_remove_task_by_id_from_user_tasks_list(self):
        user = self.create_user()
        task = user.add_task(title="Task to remove", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(user.tasks.count(), 1)
        user.remove_task(task.id)
        self.assertEqual(user.tasks.count(), 0)

    def test_remove_task_by_object_from_user_tasks_list(self):
        user = self.create_user()
        task = user.add_task(title="Task to remove", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(user.tasks.count(), 1)
        user.remove_task(task)
        self.assertEqual(user.tasks.count(), 0)

    def test_remove_task_does_not_raise_exception_when_invalid_id(self):
        user = self.create_user()
        task = user.add_task(title="Task to remove", 
                             deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(user.tasks.count(), 1)
        user.remove_task(345)
        self.assertEqual(user.tasks.count(), 1)

    def test_add_projects_creates_new_project(self):
        user = self.create_user()
        user.add_project(name="Test Project", 
                         deadline=datetime(2019, 1, 1, 0, 0))
        self.assertEqual(db.session.query(Project).count(), 1)
        self.assertEqual(user.projects[0], Project.query.one())
        self.assertEqual(db.session.query(Project).one().user, user)

    def test_add_project_returns_project(self):
        user = self.create_user()
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2019, 1, 1, 0, 0))
        self.assertEqual(project, db.session.query(Project).one())

    def test_for_preventing_commit_when_adding_project(self):
        user = self.create_user()
        project = user.add_project(name="Test Project", 
                                   deadline=datetime(2019, 1, 1, 0, 0),
                                   commit=False)
        db.session.rollback() 
        self.assertEqual(db.session.query(Project).count(), 0)
        self.assertEqual(user.projects.count(), 0)

    def test_add_project_accepts_project_object_as_first_argument(self):
        user = self.create_user()
        project = Project(name="FUCK", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        user.add_project(project)
        self.assertEqual(db.session.query(Project).count(), 1)
        self.assertEqual(user.projects.count(), 1)
        self.assertEqual(user.projects[0], project)

    def test_remove_project_by_id_from_user_projects_list(self):
        user = self.create_user()
        project = user.add_project(name="Project to remove", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(user.projects.count(), 1)
        user.remove_project(project.id)
        self.assertEqual(user.projects.count(), 0)

    def test_remove_task_by_object_from_user_tasks_list(self):
        user = self.create_user()
        project = user.add_project(name="Project to remove", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(user.projects.count(), 1)
        user.remove_project(project)
        self.assertEqual(user.projects.count(), 0)

    def test_remove_task_does_not_raise_exception_when_invalid_id(self):
        user = self.create_user()
        project = user.add_project(name="Project to remove", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(user.projects.count(), 1)
        user.remove_project(345)
        self.assertEqual(user.projects.count(), 1)


class TestTask(TestCase):

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_for_creating_event_for_new_task(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()       
        self.assertEqual(db.session.query(Event).count(), 1)
        event = db.session.query(Event).one()
        task = db.session.query(Task).one()
        self.assertEqual(event.task, task)

    def test_for_turning_off_event_for_new_task(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0),
                    deadline_event=False)
        db.session.add(task)
        db.session.commit()       
        self.assertEqual(db.session.query(Event).count(), 0)
        task = db.session.query(Task).one()
        self.assertIsNone(task.deadline_event)      

    def test_for_updating_task_with_dict(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).one()
        data = { "title": "New Task Title", "body": "Very Important" }
        task.update(data)
        db.session.rollback()
        task = db.session.query(Task).one()
        self.assertEqual(task.title, data["title"])
        self.assertEqual(task.body, data["body"])
        self.assertEqual(task.deadline, datetime(2015, 1, 1, 0, 0))

    def test_for_updating_task_with_kwargs(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).one()
        task.update(title="New Task Title", body="Very Important")
        db.session.rollback()
        task = db.session.query(Task).one()
        self.assertEqual(task.title, "New Task Title")
        self.assertEqual(task.body, "Very Important")
        self.assertEqual(task.deadline, datetime(2015, 1, 1, 0, 0))

    def test_for_updating_deadline_event_with_task(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).one()
        task.update(title="New Task Title", deadline=datetime(2018, 1, 1, 0, 0))
        event = db.session.query(Task).one().deadline_event
        self.assertEqual(event.end, datetime(2018, 1, 1, 0, 0))
        self.assertEqual(event.title, "Task 'New Task Title'")
        self.assertEqual(event.description, "Deadline of the task is on " 
                + datetime(2018, 1, 1, 0, 0).strftime("%Y-%m-%d %H:%M:%S") 
                + ".",)
        self.assertEqual(event.start, datetime(2018, 1, 1, 0, 0)  - timedelta(minutes=30))

    def test_for_preventing_commit_when_update(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).one()
        data = { "title": "New Task Title", "body": "Very Important" }
        task.update(data, commit=False)
        db.session.rollback()
        task = db.session.query(Task).one()
        self.assertEqual(task.title, "Task Title")
        self.assertIsNone(task.body)


class TestProject(TestCase):

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_for_creating_event_for_new_project(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()       
        self.assertEqual(db.session.query(Event).count(), 1)
        event = db.session.query(Event).one()
        project = db.session.query(Project).one()
        self.assertEqual(event.project, project)

    def test_for_turning_off_event_for_new_project(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0),
                          deadline_event=False)
        db.session.add(project)
        db.session.commit()       
        self.assertEqual(db.session.query(Event).count(), 0)
        self.assertIsNone(project.deadline_event)

    def test_for_updating_project_with_dict(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        project = db.session.query(Project).one()
        data = { "name": "Revolution", "description": "Very Important" }
        project.update(data)
        db.session.rollback()
        project = db.session.query(Project).one()
        self.assertEqual(project.description, data["description"])
        self.assertEqual(project.deadline, datetime(2015, 1, 1, 0, 0))

    def test_for_updating_project_with_kwargs(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        project = db.session.query(Project).one()
        project.update(name="Revolution", description="Very Important",
                       complete=True)
        db.session.rollback()
        project = db.session.query(Project).one()
        self.assertEqual(project.name, "Revolution")
        self.assertEqual(project.description, "Very Important")
        self.assertEqual(project.deadline, datetime(2015, 1, 1, 0, 0))
        self.assertEqual(project.complete, True)

    def test_for_updating_deadline_event_with_project(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        project = db.session.query(Project).one()
        project.update(name="New Project Title", 
                       deadline=datetime(2018, 1, 1, 0, 0))
        event = db.session.query(Project).one().deadline_event
        self.assertEqual(event.end, datetime(2018, 1, 1, 0, 0))
        self.assertEqual(event.title, "Project 'New Project Title'")
        self.assertEqual(event.description, "Deadline of the project is on " 
                + datetime(2018, 1, 1, 0, 0).strftime("%Y-%m-%d %H:%M:%S") 
                + ".",)
        self.assertEqual(event.start, datetime(2018, 1, 1, 0, 0)  - timedelta(minutes=30))

    def test_for_preventing_commit_when_updating(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        project = db.session.query(Project).one()
        data = { "name": "New Title", "description": "Very Important" }
        project.update(data, commit=False)
        db.session.rollback()
        project = db.session.query(Project).one()
        self.assertEqual(project.name, "Sample Project")
        self.assertIsNone(project.description)