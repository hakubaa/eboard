import sys
from datetime import datetime, timedelta
import unittest

from flask_testing import TestCase #http://pythonhosted.org/Flask-Testing/
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from app import create_app, db
from app.models import User, Task, Event, Project, Milestone, Tag, Note


class ModelTestCase(TestCase):

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all() 


class TestUser(ModelTestCase):

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

    def test_remove_project_by_object_from_user_tasks_list(self):
        user = self.create_user()
        project = user.add_project(name="Project to remove", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(user.projects.count(), 1)
        user.remove_project(project)
        self.assertEqual(user.projects.count(), 0)

    def test_remove_project_does_not_raise_exception_when_invalid_id(self):
        user = self.create_user()
        project = user.add_project(name="Project to remove", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(user.projects.count(), 1)
        user.remove_project(345)
        self.assertEqual(user.projects.count(), 1)

    def test_add_note_creates_new_note_for_user(self):
        user = self.create_user()
        user.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(db.session.query(Note).count(), 1)
        self.assertEqual(user.notes[0], Note.query.one())
        self.assertEqual(db.session.query(Note).one().user, user)

    def test_passes_args_to_add_note(self):
        user = self.create_user()
        note = user.add_note(title="Test Note", body="Very interesting note.")
        note = user.notes[0]
        self.assertEqual(note.title, "Test Note")
        self.assertEqual(note.body, "Very interesting note.")

    def test_add_note_returns_note(self):
        user = self.create_user()
        note = user.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(note, db.session.query(Note).one())

    def test_for_preventing_commit_when_adding_note(self):
        user = self.create_user()
        note = user.add_note(title="Test Note", body="Very interesting note.",
                             commit=False)
        db.session.rollback() 
        self.assertEqual(db.session.query(Note).count(), 0)
        self.assertEqual(user.notes.count(), 0)

    def test_for_commiting_when_adding_note(self):
        user = self.create_user()
        note = user.add_note(title="Test Note", body="Very interesting note.")
        db.session.rollback()
        self.assertEqual(db.session.query(Note).count(), 1)
        self.assertEqual(db.session.query(Note).one().user, user)

    def test_add_note_accepts_note_object_as_first_argument(self):
        user = self.create_user()
        note = user.add_note(title="Test Note", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()
        user.add_note(note)
        self.assertEqual(db.session.query(Note).count(), 1)
        self.assertEqual(user.notes.count(), 1)
        self.assertEqual(user.notes[0], note)

    def test_remove_note_by_id_from_user_notes_list(self):
        user = self.create_user()
        note = user.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(user.notes.count(), 1)
        user.remove_note(note.id)
        self.assertEqual(user.notes.count(), 0)

    def test_remove_note_by_object_from_user_tasks_list(self):
        user = self.create_user()
        note = user.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(user.notes.count(), 1)
        user.remove_note(note)
        self.assertEqual(user.notes.count(), 0)

    def test_remove_note_does_not_raise_exception_when_invalid_id(self):
        user = self.create_user()
        note = user.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(user.notes.count(), 1)
        user.remove_note(345)
        self.assertEqual(user.notes.count(), 1)

    @unittest.skip
    def test_for_ignoring_redundant_fields_when_creating_user(self):
        user = User(username="Test", password="test", rubbish1="AJV*S3FK",
                    rubbish2="SVK33FJF_SV")
        db.session.add(user)
        db.session.commit()
        self.assertEqual(db.session.query(User).count(), 1)
        
    def test_add_event_creates_new_event_for_user(self):
        user = self.create_user()
        event = Event(title="My First Event", start=datetime(2017, 1, 1, 0, 0),
                      end=datetime(2017, 1, 1, 12, 0))
        user.add_event(event)
        self.assertEqual(db.session.query(Event).count(), 1)
        self.assertEqual(user.events.count(), 1)
        self.assertEqual(user.events[0], Event.query.one())
        self.assertEqual(db.session.query(Event).one().user, user)

    def test_passes_args_to_add_event(self):
        user = self.create_user()
        user.add_event(title="My First Event", start=datetime(2017, 1, 1, 0, 0),
                       end=datetime(2017, 1, 1, 12, 0))
        event = user.events[0]
        self.assertEqual(event.title, "My First Event")
        self.assertEqual(event.end, datetime(2017, 1, 1, 12, 0))

    def test_add_event_returns_event(self):
        user = self.create_user()
        event = user.add_event(title="Event", start=datetime(2017, 1, 1, 0, 0), 
                               end=datetime(2017, 1, 1, 12, 0))
        self.assertEqual(event, db.session.query(Event).one())

    def test_for_preventing_commit_when_adding_event(self):
        user = self.create_user()
        event = user.add_event(title="Event", start=datetime(2017, 1, 1, 0, 0), 
                               end=datetime(2017, 1, 1, 12, 0), commit=False)
        db.session.rollback() 
        self.assertEqual(db.session.query(Event).count(), 0)
        self.assertEqual(user.events.count(), 0)

    def test_add_task_links_user_to_deadline_event(self):
        user = self.create_user()
        task = Task(title="Test Task", deadline=datetime(2017, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()
        user.add_task(task)
        self.assertEqual(db.session.query(Event).count(), 1)
        self.assertEqual(user.events.count(), 1)
        self.assertEqual(user.events[0], task.deadline_event)

    def test_remove_task_unlinks_user_from_deadline_event(self):
        user = self.create_user()
        task = Task(title="Test Task", deadline=datetime(2017, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()
        user.add_task(task)
        self.assertEqual(user.events.count(), 1)
        user.remove_task(task)
        self.assertEqual(user.events.count(), 0)

    def test_add_project_links_user_to_deadline_event(self):
        user = self.create_user()
        project = Project(name="Test Project", 
                          deadline=datetime(2017, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        user.add_project(project)
        self.assertEqual(db.session.query(Event).count(), 1)
        self.assertEqual(user.events.count(), 1)
        self.assertEqual(user.events[0], project.deadline_event)

    def test_remove_project_unliks_user_to_deadline_event(self):
        user = self.create_user()
        project = Project(name="Test Project", deadline=datetime(2017, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        user.add_project(project)
        self.assertEqual(user.events.count(), 1)
        user.remove_project(project)
        self.assertEqual(user.events.count(), 0)


class TestTask(ModelTestCase):

    def test_for_creating_event_for_new_task(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()       
        self.assertEqual(db.session.query(Event).count(), 1)
        event = db.session.query(Event).one()
        task = db.session.query(Task).one()
        self.assertEqual(event.task, task)

    def test_accepts_string_for_boolean_fields(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0),
                    complete="TRUE", active="YES")
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).one()
        self.assertTrue(task.complete)
        self.assertTrue(task.active)
        task.active = "NO"
        task.complete = False
        db.session.commit()
        self.assertFalse(task.active)
        self.assertFalse(task.complete)

    def test_accepts_strings_for_int_fields(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0),
                    importance="10", urgency="5")
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).one()
        self.assertEqual(task.importance, 10)
        self.assertEqual(task.urgency, 5)
        task.importance = "7"
        task.urgency = 6
        db.session.commit()
        self.assertEqual(task.importance, 7)
        self.assertEqual(task.urgency, 6)    

    def test_accepts_deadline_as_string(self):
        task = Task(title="Test Title", deadline="2015-01-01 00:00")
        db.session.add(task)
        db.session.commit()
        self.assertEqual(task.deadline, datetime(2015, 1, 1, 0, 0))  

    def test_for_assigning_tags_to_task_in_constructor(self):
        tag1 = Tag(name="Tag1")
        tag2 = Tag(name="Tag2")
        db.session.add(tag1)
        db.session.add(tag2)
        db.session.commit()
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0),
                    tags=[tag1, tag2])
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).one()
        self.assertEqual(len(task.tags), 2)
        self.assertIn(tag1, task.tags)
        self.assertIn(tag2, task.tags)

    def test_for_initializing_tags_by_string_values(self):
        tag1 = Tag(name="Tag1")
        tag2 = Tag(name="Tag2")
        db.session.add(tag1)
        db.session.add(tag2)
        db.session.commit()
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0),
                    tags=["Tag1", "Tag2"])
        db.session.add(task)
        db.session.commit()
        task = db.session.query(Task).one()
        self.assertEqual(len(task.tags), 2)
        self.assertIn(tag1, task.tags)
        self.assertIn(tag2, task.tags)

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
        self.assertEqual(event.desc, "Deadline of the task is on " 
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

    def test_for_assigning_tag_to_task_by_string(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()    
        task.add_tag("Test")
        db.session.rollback()
        task = db.session.query(Task).one()
        self.assertEqual(len(task.tags), 1)
        self.assertEqual(task.tags[0].name, "Test")    

    def test_for_assigning_tag_to_task_by_object(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        tag = Tag(name="Test")
        db.session.add(task)
        db.session.add(tag)
        db.session.commit()
        task.add_tag(tag)    
        task = db.session.query(Task).one()
        self.assertEqual(len(task.tags), 1)
        self.assertEqual(task.tags[0].name, "Test")    

    def test_add_tag_does_not_create_new_tag_but_raise_error(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()    
        with self.assertRaises(NoResultFound):
            task.add_tag("Test", create_new_tag=False)

    def test_for_remove_tag_from_task_by_string(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()    
        task.add_tag("Test")
        task = db.session.query(Task).one()
        task.remove_tag("TesT")
        self.assertEqual(len(task.tags), 0)
        self.assertEqual(db.session.query(Tag).count(), 1)

    def test_for_remove_tag_from_task_by_object(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()    
        task.add_tag("Test")
        task = db.session.query(Task).one()
        tag = db.session.query(Tag).one()
        task.remove_tag(tag)
        self.assertEqual(len(task.tags), 0)
        self.assertEqual(db.session.query(Tag).count(), 1)

    def test_for_ignoring_redundant_fields_when_creating_task(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0),
                    rubbish1="SDKFJSDF", rubbish2=10)
        db.session.add(task)
        db.session.commit()
        self.assertEqual(db.session.query(Task).count(), 1)

    def test_update_ignores_redundant_fields(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()
        task.update(rubbish1="SCV73KDV", rubbish2=[1, 2, 3])

    def test_for_updating_tags_with_string_values(self):
        task = Task(title="Task Title", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(task)
        db.session.commit()
        task.update(tags=["Tag1", "Tag2"])
        self.assertEqual(len(task.tags), 2)


class TestProject(ModelTestCase):

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
        data = { "name": "Revolution", "desc": "Very Important" }
        project.update(data)
        db.session.rollback()
        project = db.session.query(Project).one()
        self.assertEqual(project.desc, data["desc"])
        self.assertEqual(project.deadline, datetime(2015, 1, 1, 0, 0))

    def test_for_updating_project_with_kwargs(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        project = db.session.query(Project).one()
        project.update(name="Revolution", desc="Very Important",
                       complete=True)
        db.session.rollback()
        project = db.session.query(Project).one()
        self.assertEqual(project.name, "Revolution")
        self.assertEqual(project.desc, "Very Important")
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
        self.assertEqual(event.desc, "Deadline of the project is on " 
                + datetime(2018, 1, 1, 0, 0).strftime("%Y-%m-%d %H:%M:%S") 
                + ".",)
        self.assertEqual(event.start, datetime(2018, 1, 1, 0, 0)  - timedelta(minutes=30))

    def test_for_preventing_commit_when_updating(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        project = db.session.query(Project).one()
        data = { "name": "New Title", "desc": "Very Important" }
        project.update(data, commit=False)
        db.session.rollback()
        project = db.session.query(Project).one()
        self.assertEqual(project.name, "Sample Project")
        self.assertIsNone(project.desc)

    def test_add_milestone_creates_new_milestone(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        milestone = project.add_milestone(title="First Milestone")
        db.session.rollback()
        self.assertEqual(db.session.query(Milestone).count(), 1)
        self.assertEqual(project.milestones.count(), 1)
        self.assertEqual(milestone.title, "First Milestone")

    def test_add_milestone_accepts_milestone_object_as_first_argument(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        milestone = Milestone(title="Init Milestone")
        db.session.add(project)
        db.session.add(milestone)
        db.session.commit()
        project.add_milestone(milestone)
        self.assertEqual(db.session.query(Milestone).count(), 1)
        self.assertEqual(project.milestones.count(), 1)
        self.assertEqual(project.milestones[0], milestone)

    def test_add_milestone_sets_proper_position_of_milestone(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()        
        milestone1 = project.add_milestone(title="First Milestone")
        self.assertEqual(milestone1.position, 0)
        milestone2 = project.add_milestone(title="Second Milestone")
        self.assertEqual(milestone2.position, 1)
        milestone3 = Milestone(title="Third Milestone")
        project.add_milestone(milestone3)
        self.assertEqual(milestone3.position, 2)
        project.remove_milestone(milestone1)
        milestone4 = project.add_milestone(title="New Milestone")
        self.assertEqual(milestone4.position, 3)

    def test_remove_milestone_by_id_from_project_milestones_list(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        milestone = project.add_milestone(title="First Milestone")
        self.assertEqual(project.milestones.count(), 1)
        project.remove_milestone(milestone.id)
        self.assertEqual(project.milestones.count(), 0)

    def test_remove_milestone_by_object_from_project_milestones_list(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        milestone = project.add_milestone(title="First Milestone")
        self.assertEqual(project.milestones.count(), 1)
        project.remove_milestone(milestone)
        self.assertEqual(project.milestones.count(), 0)

    def test_remove_milestone_does_not_raise_exception_when_invalid_id(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        milestone = project.add_milestone(title="First Milestone")
        self.assertEqual(project.milestones.count(), 1)
        project.remove_milestone(345)
        self.assertEqual(project.milestones.count(), 1)

    def test_add_note_creates_new_note_for_user(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        project.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(db.session.query(Note).count(), 1)
        self.assertEqual(project.notes[0], Note.query.one())
        self.assertEqual(db.session.query(Note).one().project, project)

    def test_passes_args_to_add_note(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        note = project.add_note(title="Test Note", body="Very interesting note.")
        note = project.notes[0]
        self.assertEqual(note.title, "Test Note")
        self.assertEqual(note.body, "Very interesting note.")

    def test_add_note_returns_note(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        note = project.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(note, db.session.query(Note).one())

    def test_for_preventing_commit_when_adding_note(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        note = project.add_note(title="Test Note", body="Very interesting note.",
                                commit=False)
        db.session.rollback() 
        self.assertEqual(db.session.query(Note).count(), 0)
        self.assertEqual(project.notes.count(), 0)

    def test_for_commiting_when_adding_note(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        note = project.add_note(title="Test Note", body="Very interesting note.")
        db.session.rollback()
        self.assertEqual(db.session.query(Note).count(), 1)
        self.assertEqual(db.session.query(Note).one().project, project)

    def test_add_note_accepts_note_object_as_first_argument(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        note = project.add_note(title="Test Note", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()
        project.add_note(note)
        self.assertEqual(db.session.query(Note).count(), 1)
        self.assertEqual(project.notes.count(), 1)
        self.assertEqual(project.notes[0], note)

    def test_remove_note_by_id_from_user_notes_list(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        note = project.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(project.notes.count(), 1)
        project.remove_note(note.id)
        self.assertEqual(project.notes.count(), 0)

    def test_remove_note_by_object_from_user_tasks_list(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        note = project.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(project.notes.count(), 1)
        project.remove_note(note)
        self.assertEqual(project.notes.count(), 0)

    def test_remove_note_does_not_raise_exception_when_invalid_id(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        note = project.add_note(title="Test Note", body="Very interesting note.")
        self.assertEqual(project.notes.count(), 1)
        project.remove_note(345)
        self.assertEqual(project.notes.count(), 1)

    def test_for_ignoring_redundant_fields_when_creating_project(self):
        project = Project(name="Sample Project", rubbish1=range(5),
                          deadline=datetime(2015, 1, 1, 0, 0),
                          rubbish2=345)
        db.session.add(project)
        db.session.commit()
        self.assertEqual(db.session.query(Project).count(), 1)

    def test_update_ignores_redundant_fields(self):
        project = Project(name="Sample Project", 
                          deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(project)
        db.session.commit()
        project.update(rubbish1="SCV73KDV", rubbish2=[1, 2, 3])


class TestMilestone(ModelTestCase):

    def test_add_task_creates_new_task(self):
        milestone = Milestone(title="Sample Milestone")
        db.session.add(milestone)
        db.session.commit()
        task = milestone.add_task(title="First Task", 
                                  deadline=datetime(2015, 1, 1, 0, 0))
        db.session.rollback()
        self.assertEqual(db.session.query(Task).count(), 1)
        self.assertEqual(milestone.tasks.count(), 1)
        self.assertEqual(task.title, "First Task")

    def test_add_task_accepts_task_object_as_first_argument(self):
        milestone = Milestone(title="Sample Milestone")
        task = Task(title="First Task", deadline=datetime(2015, 1, 1, 0, 0))
        db.session.add(milestone)
        db.session.add(task)
        db.session.commit()
        milestone.add_task(task)
        self.assertEqual(milestone.tasks.count(), 1)
        self.assertEqual(milestone.tasks.one().title, "First Task")

    def test_for_updating_milestone_with_data_in_dict(self):
        milestone = Milestone(title="Sample Milestone", desc="Milestone",
                              position=99)
        db.session.add(milestone)
        db.session.commit()
        milestone.update({"title": "Super Milestone", "desc": "Power",
                          "position": 0})
        self.assertEqual(milestone.title, "Super Milestone")
        self.assertEqual(milestone.desc, "Power")
        self.assertEqual(milestone.position, 0)

    def test_for_updating_milestone_with_kwargs(self):
        milestone = Milestone(title="Sample Milestone", desc="Milestone",
                              position=99)
        db.session.add(milestone)
        db.session.commit()
        milestone.update(title="Super Milestone", desc="Power", position=0)
        self.assertEqual(milestone.title, "Super Milestone")
        self.assertEqual(milestone.desc, "Power")
        self.assertEqual(milestone.position, 0)

    def test_remove_task_by_id_from_milestone_tasks_list(self):
        milestone = Milestone(title="Sample Milestone")
        db.session.add(milestone)
        db.session.commit()
        task = milestone.add_task(title="First Task", 
                                  deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(milestone.tasks.count(), 1)
        milestone.remove_task(task.id)
        self.assertEqual(milestone.tasks.count(), 0)
        self.assertEqual(db.session.query(Task).count(), 0)

    def test_remove_milestone_by_object_from_project_milestones_list(self):
        milestone = Milestone(title="Sample Milestone")
        db.session.add(milestone)
        db.session.commit()
        task = milestone.add_task(title="First Task", 
                                  deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(milestone.tasks.count(), 1)
        milestone.remove_task(task)
        self.assertEqual(milestone.tasks.count(), 0)

    def test_remove_milestone_does_not_raise_exception_when_invalid_id(self):
        milestone = Milestone(title="Sample Milestone")
        db.session.add(milestone)
        db.session.commit()
        task = milestone.add_task(title="First Task", 
                                  deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(milestone.tasks.count(), 1)
        milestone.remove_task(34534)
        self.assertEqual(milestone.tasks.count(), 1)

    def test_for_ignoring_redundant_fields_when_creating_milestone(self):
        milestone = Milestone(title="Sample Milestone", rubbish1=9,
                              nofield="UNKNOWN")
        db.session.add(milestone)
        db.session.commit()
        self.assertEqual(db.session.query(Milestone).count(), 1)

    def test_update_ignores_redundant_fields(self):
        milestone = Milestone(title="Sample Milestone")
        db.session.add(milestone)
        db.session.commit()
        milestone.update(rubbish1="SCV73KDV", rubbish2=[1, 2, 3])

    def test_for_moving_task_between_milestones(self):
        milestone1 = Milestone(title ="Milestone 1")
        milestone2 = Milestone(title="Milestone 2")
        db.session.add(milestone1)
        db.session.add(milestone2)
        db.session.commit()
        task = milestone1.add_task(title="My First Task", 
                                   deadline=datetime(2015, 1, 1, 0, 0))
        self.assertEqual(milestone1.tasks.count(), 1)
        self.assertEqual(milestone2.tasks.count(), 0)
        task.update(milestone_id=milestone2.id)
        self.assertEqual(milestone1.tasks.count(), 0)
        self.assertEqual(milestone2.tasks.count(), 1)
                

class TestTag(ModelTestCase):

    def test_creates_new_tag_with_find_or_create(self):
        tag = Tag.find_or_create(name="Test")
        self.assertEqual(db.session.query(Tag).count(), 1)
        self.assertEqual(db.session.query(Tag).one().name, "Test")

    def test_does_not_create_new_tag_when_similar_tag_exists(self):
        tag = Tag.find_or_create(name="Test")
        tag = Tag.find_or_create(name="TEST")
        self.assertEqual(db.session.query(Tag).count(), 1)
        self.assertEqual(db.session.query(Tag).one().name, "Test")

    def test_for_preveing_commit_when_create_new_tag(self):
        tag = Tag.find_or_create(name="Test", commit=False)
        db.session.rollback()
        self.assertEqual(db.session.query(Tag).count(), 0)

    def test_for_preventing_tag_creation(self):
        tag = Tag.find_or_create(name="Test", create_new_tag=False)
        self.assertIsNone(tag)

    def test_for_ignoring_redundant_fields_when_creating_tag(self):
        tag = Tag(name="Test", rubbish1=1, rubbish2=(1, 2, 3))
        db.session.add(tag)
        db.session.commit()
        self.assertEqual(db.session.query(Tag).count(), 1)


class TestNote(ModelTestCase):

    def test_for_assigning_tags_to_note_in_constructor(self):
        tag1 = Tag(name="Tag1")
        tag2 = Tag(name="Tag2")
        db.session.add(tag1)
        db.session.add(tag2)
        db.session.commit()
        note = Note(title="Note Title", body="Very interesting note.",
                    tags=[tag1, tag2])
        db.session.add(note)
        db.session.commit()
        note = db.session.query(Note).one()
        self.assertEqual(len(note.tags), 2)
        self.assertIn(tag1, note.tags)
        self.assertIn(tag2, note.tags)  

    def test_for_initializing_tags_by_string_values(self):
        tag1 = Tag(name="Tag1")
        tag2 = Tag(name="Tag2")
        db.session.add(tag1)
        db.session.add(tag2)
        db.session.commit()
        note = Note(title="Note Title", body="Very interseting note.",
                    tags=["Tag1", "Tag2"])
        db.session.add(note)
        db.session.commit()
        note = db.session.query(Note).one()
        self.assertEqual(len(note.tags), 2)
        self.assertIn(tag1, note.tags)
        self.assertIn(tag2, note.tags)

    def test_for_updating_note_with_dict(self):
        tag1 = Tag(name="Tag1")
        tag2 = Tag(name="Tag2")
        db.session.add(tag1)
        db.session.add(tag2)
        note = Note(title="Note Title", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()

        note = db.session.query(Note).one()
        data = { "title": "New Note Title", "tags": [tag1, tag2] }
        note.update(data)
        db.session.rollback()

        note = db.session.query(Note).one()
        self.assertEqual(note.title, data["title"])
        self.assertIn(tag1, note.tags)
        self.assertIn(tag2, note.tags)

    def test_for_updating_note_with_kwargs(self):
        tag1 = Tag(name="Tag1")
        tag2 = Tag(name="Tag2")
        db.session.add(tag1)
        db.session.add(tag2)
        note = Note(title="Note Title", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()

        note = db.session.query(Note).one()
        note.update(title="New Note Title", tags=[tag1, tag2])
        db.session.rollback()

        note = db.session.query(Note).one()
        self.assertEqual(note.title, "New Note Title")
        self.assertIn(tag1, note.tags)
        self.assertIn(tag2, note.tags)

    def test_for_preventing_commit_when_update(self):
        tag1 = Tag(name="Tag1")
        tag2 = Tag(name="Tag2")
        db.session.add(tag1)
        db.session.add(tag2)
        note = Note(title="Note Title", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()
        note = db.session.query(Note).one()
        note.update(title="New Note Title", tags=[tag1, tag2], commit=False)
        db.session.rollback()
        note = db.session.query(Note).one()
        self.assertEqual(note.title, "Note Title")
        self.assertFalse(note.tags)

    def test_for_assigning_tag_to_note_by_string(self):
        note = Note(title="Note Title", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()    
        note.add_tag("Test")
        db.session.rollback()
        note = db.session.query(Note).one()
        self.assertEqual(len(note.tags), 1)
        self.assertEqual(note.tags[0].name, "Test")    

    def test_for_assigning_tag_to_note_by_object(self):
        note = Note(title="Note Title", body="Very interesting note.")
        tag = Tag(name="Test")
        db.session.add(note)
        db.session.add(tag)
        db.session.commit()
        note.add_tag(tag)    
        note = db.session.query(Note).one()
        self.assertEqual(len(note.tags), 1)
        self.assertEqual(note.tags[0].name, "Test")    

    def test_add_tag_does_not_create_new_tag_but_raise_error(self):
        note = Note(title="Note Title", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()    
        with self.assertRaises(NoResultFound):
            note.add_tag("Test", create_new_tag=False)

    def test_for_remove_tag_from_note_by_string(self):
        note = Note(title="Note Title", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()    
        note.add_tag("Test")
        note = db.session.query(Note).one()
        note.remove_tag("TesT")
        self.assertEqual(len(note.tags), 0)
        self.assertEqual(db.session.query(Tag).count(), 1)

    def test_for_remove_tag_from_note_by_object(self):
        note = Note(title="Note Title", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()    
        note.add_tag("Test")
        note = db.session.query(Note).one()
        tag = db.session.query(Tag).one()
        note.remove_tag(tag)
        self.assertEqual(len(note.tags), 0)
        self.assertEqual(db.session.query(Tag).count(), 1)

    def test_for_ignoring_redundant_fields_when_creating_note(self):
        note = Note(title="Note Title", body="Very interesting note.",
                    deadline=datetime(2015, 1, 1, 0, 0), complete=True)
        db.session.add(note)
        db.session.commit()    
        self.assertEqual(db.session.query(Note).count(), 1)

    def test_update_ignores_redundant_fields(self):
        note = Note(title="Note Title", body="Very interesting note.")
        db.session.add(note)
        db.session.commit()
        note.update(deadline=datetime(2017, 1, 1, 0, 0), active=False)

    def test_for_updating_tags_by_string_values(self):
        note = Note(title="First Note", body="Very Interesting Note.")
        db.session.add(note)
        db.session.commit()
        note.update(tags=["tag1", "tag2", "tag3"])
        self.assertEqual(len(note.tags), 3)


class TestEvent(ModelTestCase):

    def test_for_ignoring_redundant_fields_when_creating_event(self):
        event = Event(title="Sample Event", start=datetime(2017, 1, 1, 0, 0),
                      end=datetime(2018, 1, 1, 0, 0), rubbish1=9,
                      nofield="UNKNOWN")
        db.session.add(event)
        db.session.commit()
        self.assertEqual(db.session.query(Event).count(), 1)
        event = db.session.query(Event).one()
        self.assertEqual(event.title, "Sample Event")
        with self.assertRaises(AttributeError):
            self.assertIsNone(event.rubbish1)

    def test_for_updating_event_with_update_method(self):
        event = Event(title="Sample Event", start=datetime(2017, 1, 1, 0, 0),
                      end=datetime(2018, 1, 1, 0, 0), rubbish1=9,
                      nofield="UNKNOWN")
        db.session.add(event)
        db.session.commit()
        event.update(title="New Event's Title", end=datetime(2017, 1, 1, 12, 0))
        event = db.session.query(Event).one()
        self.assertEqual(event.title, "New Event's Title")
        self.assertEqual(event.end, datetime(2017, 1, 1, 12, 0))

    def test_update_ignores_redundant_fields(self):
        event = Event(title="Sample Event", start=datetime(2017, 1, 1, 0, 0),
                      end=datetime(2018, 1, 1, 0, 0), rubbish1=9,
                      nofield="UNKNOWN")
        db.session.add(event)
        db.session.commit()
        event.update(title="New Event's Title", rubbish1="Test", rubbish2=2)

    def test_update_raises_error_when_positional_argument_is_not_dict(self):
        event = Event(title="Sample Event", start=datetime(2017, 1, 1, 0, 0),
                      end=datetime(2018, 1, 1, 0, 0), rubbish1=9,
                      nofield="UNKNOWN")
        db.session.add(event)
        db.session.commit()
        with self.assertRaises(TypeError):
            event.update("New Event's Title")

