import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import redirect, url_for
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from app import db
from app.utils import merge_dicts


# Association table for notes & tags
taskstags = db.Table("taskstags",
    db.Column("task_id", db.Integer, db.ForeignKey("tasks.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"))
    )

# Associate tables for notes & tags
notestags = db.Table("notestags",
    db.Column("note_id", db.Integer, db.ForeignKey("notes.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"))
    )


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256))
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    deadline = db.Column(db.DateTime)
    notes = db.Column(db.String()) #remove
    body = db.Column(db.String())
    importance = db.Column(db.Integer)
    urgency = db.Column(db.Integer)
    active = db.Column(db.Boolean(), default=True)
    complete = db.Column(db.Boolean(), default=False)

    tags = db.relationship("Tag", secondary=taskstags, lazy="immediate")

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates = "tasks")

    milestone_id = db.Column(db.Integer, db.ForeignKey("milestones.id"))
    milestone = db.relationship("Milestone", back_populates = "tasks")

    deadline_event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    deadline_event = db.relationship("Event", back_populates = "task",
        cascade = "all, delete, delete-orphan", single_parent = True)

    def __init__(self, *args, deadline_event=True, **kwargs):
        super().__init__(*args, **kwargs)
        if deadline_event:
            self.deadline_event = Event(
                    title = "Task '" + self.title + "'", 
                    start = self.deadline - datetime.timedelta(minutes=30),
                    end = self.deadline, className = "fc-task-deadline",
                    desc = "Deadline of the task is on " 
                    + self.deadline.strftime("%Y-%m-%d %H:%M:%S") + ".",
                    editable = False
                )

    def update(self, data=None, commit=True, **kwargs):
        '''
        Update task on the base of dict or **kwargs.
        '''
        if not data:
            data = kwargs

        # Update fields which can be update (not read-only fields)
        update_possible = {"title", "deadline", "body", "importance", 
                           "urgency", "active", "complete", "tags"}
        fields_to_update = update_possible & set(data.keys())
        for field in fields_to_update:
            setattr(self, field, data[field])

        # Update deadline event connected with task
        if self.deadline_event:
            if "title" in data:
                self.deadline_event.title = "Task '" + self.title + "'"
            if "deadline" in data:
                self.deadline_event.start = self.deadline - \
                                            datetime.timedelta(minutes=30)
                self.deadline_event.end = self.deadline
                self.deadline_event.desc = \
                            "Deadline of the task is on " + \
                            self.deadline.strftime("%Y-%m-%d %H:%M:%S") + "."

        if commit:
            db.session.commit()

    def add_tag(self, tag, commit=True, create_new_tag=True):
        '''
        Adds tag to task. Creates new tag if does not exist.
        '''
        if isinstance(tag, Tag):
            tag_obj = tag
        else:
            tag_obj = Tag.find_or_create(name=tag, commit=commit, 
                                         create_new_tag=create_new_tag)
        if not tag_obj:
            raise NoResultFound("Tag '%s' does not exist." % tag)
        self.tags.append(tag_obj)
        if commit:
            db.session.commit()
        return tag_obj

    def remove_tag(self, tag, commit=True):
        '''
        Removes tag from task. 
        '''
        if isinstance(tag, Tag):
            tag_obj = [item for item in self.tags if item == tag]
        else:
            tag_obj = [item for item in self.tags 
                            if item.name.lower() == tag.lower()]
        if tag_obj:
            self.tags.remove(tag_obj[0])

    def to_dict(self):
        return {
                "title": self.title, 
                "created": self.created.strftime("%Y-%m-%d %H:%M:%S"),
                "deadline": self.deadline.strftime("%Y-%m-%d %H:%M:%S"),
                "notes": self.notes, 
                "tags": [ tag.to_dict() for tag in self.tags ],
                "complete": self.complete, "active": self.active,
                "daysleft": self.daysleft, "id": self.id, 
                "importance": self.importance,
                "urgency": self.urgency 
             }

    def get_info(self):
        return {
                "title": self.title, 
                "created": self.created.strftime("%Y-%m-%d %H:%M:%S"),
                "deadline": self.deadline.strftime("%Y-%m-%d %H:%M:%S"),
                "complete": self.complete, "active": self.active,
                "daysleft": self.daysleft, "id": self.id
             }

    @property
    def daysleft(self):
        return (self.deadline - datetime.datetime.now()).days


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    tasks = db.relationship("Task", secondary = taskstags)
    notes = db.relationship("Note", secondary = notestags)

    @staticmethod
    def find_or_create(name, commit=True, create_new_tag=True):
        tag = db.session.query(Tag).filter(
                func.lower(Tag.name) == func.lower(name)).first()
        if not tag and create_new_tag:
            tag = Tag(name=name)
            db.session.add(tag)
            if commit:
                db.session.commit()
        return tag

    def to_dict(self): 
        return { "id": self.id, "name": self.name }

    def get_info(self):
        return self.to_dict()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    public = db.Column(db.Boolean(), unique=False, default=False)

    tasks = db.relationship("Task", back_populates="user",
        cascade = "all, delete, delete-orphan", lazy="dynamic")
    projects = db.relationship("Project", back_populates="user",
        cascade = "all, delete, delete-orphan", lazy="dynamic")
    notes = db.relationship("Note", back_populates="user",
        cascade = "all, delete, delete-orphan", lazy="dynamic")

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_task(self, *args, commit=True, **kwargs):
        '''
        Adds task to user's task list. Checks whether the first position
        argument is Task object.
        '''
        if len(args) > 0 and isinstance(args[0], Task):
            task = args[0]
        else:
            task = Task(*args, **kwargs)
            db.session.add(task)

        self.tasks.append(task)
        if commit:
            db.session.commit()
        return task

    def remove_task(self, task):
        '''
        Removes task from user's task list. Check whether the first position
        is instance of Task or id.
        '''
        if not isinstance(task, Task):
            task = Task.query.get(task)
        if task:
            self.tasks.remove(task)

    def add_project(self, *args, commit=True, **kwargs):
        '''
        Creates new project for the user. Checks whether the first position
        argument is Project object.
        '''
        if len(args) > 0 and isinstance(args[0], Project):
            project = args[0]
        else:
            project = Project(*args, **kwargs)
            db.session.add(project)

        self.projects.append(project)
        if commit:
            db.session.commit()
        return project

    def remove_project(self, project):
        '''
        Removes project. Checks whether the first position is instance of 
        Project or id.
        '''
        if not isinstance(project, Project):
            project = Project.query.get(project)
        if project:
            self.projects.remove(project)

    def add_note(self, *args, commit=True, **kwargs):
        '''
        Adds note to user's notes list. Checks whether the first position
        argument is Note object.
        '''
        if len(args) > 0 and isinstance(args[0], Note):
            note = args[0]
        else:
            note = Note(*args, **kwargs)
            db.session.add(note)

        self.notes.append(note)
        if commit:
            db.session.commit()
        return note

    def remove_note(self, note):
        '''
        Removes note. Checks whether the first position is instance of 
        Note or id.
        '''
        if not isinstance(note, Note):
            note = Note.query.get(note)
        if note:
            self.notes.remove(note)

    def to_dict(self):
        return {
            "id": self.id, "email": self.email,
            "username": self.username, "public": self.public,
            "tasks": [ task.get_info() for task in self.tasks ],
            "projects": [ project.get_info() for project in self.projects ],
            "notes": [ note.get_info() for note in self.notes ]
            }

    def get_info(self):
        return {
            "id": self.id, "email": self.email,
            "username": self.username, "public": self.public
            }      

    def __repr__(self):
        return '<User %r>' % self.username


class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, 
                          default=datetime.datetime.utcnow)
    tags = db.relationship("Tag", secondary=notestags, lazy="immediate")
    
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"));
    project = db.relationship("Project", back_populates="notes")

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates = "notes")

    def update(self, data=None, commit=True, **kwargs):
        '''
        Update note on the base of dict or **kwargs.
        '''
        if not data:
            data = kwargs

        # Update fields which can be update (not read-only fields)
        update_possible = {"title", "body", "tags"}
        fields_to_update = update_possible & set(data.keys())
        for field in fields_to_update:
            setattr(self, field, data[field])

        if commit:
            db.session.commit()

    def add_tag(self, tag, commit=True, create_new_tag=True):
        '''
        Adds tag to note. Creates new tag if does not exist.
        '''
        if isinstance(tag, Tag):
            tag_obj = tag
        else:
            tag_obj = Tag.find_or_create(name=tag, commit=commit, 
                                         create_new_tag=create_new_tag)
        if not tag_obj:
            raise NoResultFound("Tag '%s' does not exist." % tag)
        self.tags.append(tag_obj)
        if commit:
            db.session.commit()
        return tag_obj

    def remove_tag(self, tag, commit=True):
        '''
        Removes tag from note. 
        '''
        if isinstance(tag, Tag):
            tag_obj = [item for item in self.tags if item == tag]
        else:
            tag_obj = [item for item in self.tags 
                            if item.name.lower() == tag.lower()]
        if tag_obj:
            self.tags.remove(tag_obj[0])

    def to_dict(self):
        return { 
            "id": self.id, "title": self.title, "body": self.body,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "tags": [ tag.to_dict() for tag in self.tags ]
            }

    def get_info(self):
        return { 
            "id": self.id, "title": self.title,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }

class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    desc = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    active = db.Column(db.Boolean(), default=True)
    complete = db.Column(db.Boolean(), default=False)

    milestones = db.relationship("Milestone", back_populates="project",
        cascade = "all, delete, delete-orphan", lazy="dynamic")
    notes = db.relationship("Note", back_populates="project",
        cascade = "all, delete, delete-orphan", lazy="dynamic")

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates = "projects")

    deadline_event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    deadline_event = db.relationship("Event", back_populates = "project",
        cascade = "all, delete, delete-orphan", single_parent = True)

    def __init__(self, *args, deadline_event=True, **kwargs):
        super().__init__(*args, **kwargs)
        if deadline_event:
            self.deadline_event = Event(
                title = "Project '" + self.name + ",", 
                start = self.deadline - datetime.timedelta(minutes=30),
                end = self.deadline,
                className = "fc-project-deadline",
                desc = "Deadline of the project is set on " + 
                    self.deadline.strftime("%Y-%m-%d %H:%M:%S") + ".",
                editable = False)


    def update(self, data=None, commit=True, **kwargs):
        '''
        Update project on the base of dict or **kwargs.
        '''
        if not data:
            data = kwargs

        # Update fields which can be update (not read-only fields)
        update_possible = {"name", "desc", "deadline", 
                           "active", "complete"}
        fields_to_update = update_possible & set(data.keys())
        for field in fields_to_update:
            setattr(self, field, data[field])

        # Update deadline event connected with task
        if self.deadline_event:
            if "name" in data:
                self.deadline_event.title = "Project '" + self.name + "'"
            if "deadline" in data:
                self.deadline_event.start = self.deadline - \
                                            datetime.timedelta(minutes=30)
                self.deadline_event.end = self.deadline
                self.deadline_event.desc = \
                            "Deadline of the project is on " + \
                            self.deadline.strftime("%Y-%m-%d %H:%M:%S") + "."

        if commit:
            db.session.commit()

    def add_milestone(self, *args, commit=True, **kwargs):
        '''
        Adds new milestone to the project and sets it position after
        last milestone.
        '''
        if len(args) > 0 and isinstance(args[0], Milestone):
            milestone = args[0]
        else:
            milestone = Milestone(*args, **kwargs)
        db.session.add(milestone)

        # Update mileston position
        if self.milestones.count() > 0:
            last_position = db.session.query(func.max(Milestone.position)) \
                                      .filter(Milestone.project_id == self.id) \
                                      .one()
            milestone.position = last_position[0] + 1

        self.milestones.append(milestone)
        if commit:
            db.session.commit()
        return milestone

    def remove_milestone(self, milestone):
        '''
        Removes milestone from the project. Check whether the first position
        is instance of Milestone or id.
        '''
        if not isinstance(milestone, Milestone):
            milestone = Milestone.query.get(milestone)
        if milestone:
            self.milestones.remove(milestone)

    def add_note(self, *args, commit=True, **kwargs):
        '''
        Adds note to project's notes list. Checks whether the first position
        argument is Note object.
        '''
        if len(args) > 0 and isinstance(args[0], Note):
            note = args[0]
        else:
            note = Note(*args, **kwargs)
            db.session.add(note)

        self.notes.append(note)
        if commit:
            db.session.commit()
        return note

    def remove_note(self, note):
        '''
        Removes note. Checks whether the first position is instance of 
        Note or id.
        '''
        if not isinstance(note, Note):
            note = Note.query.get(note)
        if note:
            self.notes.remove(note)

    def to_dict(self):
         return {
            "id": self.id, "name": self.name, 
            "active": self.active, "complete": self.complete,
            "desc": self.desc,
            "deadline": self.deadline.strftime("%Y-%m-%d %H:%M"),
            "created": self.created.strftime("%Y-%m-%d %H:%M"),
            "modified": self.modified.strftime("%Y-%m-%d %H:%M"),
            "milestones": [ milestone.get_info() for milestone in self.milestones ],
            "notes": [ note.get_info() for note in self.notes ]
            }       

    def get_info(self):
        return {
            "id": self.id, "name": self.name, 
            "active": self.active, "complete": self.complete,
            "desc": self.desc,
            "deadline": self.deadline.strftime("%Y-%m-%d %H:%M"),
            "created": self.created.strftime("%Y-%m-%d %H:%M"),
            "modified": self.modified.strftime("%Y-%m-%d %H:%M")
            }


class Milestone(db.Model):
    __tablename__ = "milestones"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    desc = db.Column(db.Text)
    position = db.Column(db.Integer, default=0)

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    project = db.relationship("Project", back_populates="milestones")

    tasks = db.relationship("Task", back_populates="milestone",
        cascade = "all, delete, delete-orphan", lazy="dynamic")

    def add_task(self, *args, commit=True, **kwargs):
        '''
        Adds task to the milestone. Checks whether the first position
        argument is Task object.
        '''
        if len(args) > 0 and isinstance(args[0], Task):
            task = args[0]
        else:
            task = Task(*args, **kwargs)
            db.session.add(task)

        self.tasks.append(task)
        if commit:
            db.session.commit()
        return task

    def remove_task(self, task):
        '''
        Removes taks from the milestone. Check whether the first position
        is instance of Task or id.
        '''
        if not isinstance(task, Task):
            task = Task.query.get(task)
        if task:
            self.tasks.remove(task)

    def update(self, data=None, commit=True, **kwargs):
        '''
        Update milestone on the base of dict or **kwargs.
        '''
        if not data:
            data = kwargs

        # Update fields which can be update (not read-only fields)
        update_possible = {"title", "position", "desc"}
        fields_to_update = update_possible & set(data.keys())
        for field in fields_to_update:
            setattr(self, field, data[field])

        if commit:
            db.session.commit()

    def to_dict(self):
        return { 
            "id": self.id, "title": self.title, 
            "desc": self.desc, "position": self.position,
            # "project_id": self.project_id, 
            "tasks": [ task.get_info() for task in self.tasks ]
            }

    def get_info(self):
        return { 
            "id": self.id, "title": self.title, 
            "desc": self.desc, "position": self.position,
            # "project_id": self.project_id, 
            }


class Event(db.Model):
    __tablename__ = "events"
    # Event Object http://fullcalendar.io/docs/event_data/Event_Object/
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String)
    allDay = db.Column(db.Boolean, default = False)
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    editable = db.Column(db.Boolean, default = True)
    url = db.Column(db.String)

    className = db.Column(db.String)
    color = db.Column(db.String)
    textColor = db.Column(db.String)
    backgroundColor = db.Column(db.String)
    borderColor = db.Column(db.String)

    # Extra fields
    desc = db.Column(db.String)

    # Relationships
    task = db.relationship("Task", back_populates = "deadline_event", 
        uselist = False)
    project = db.relationship("Project", back_populates = "deadline_event", 
        uselist = False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "allDay": self.allDay,
            "start": self.start.strftime("%Y-%m-%d %H:%M:%S"),
            "end": self.end.strftime("%Y-%m-%d %H:%M:%S"),
            "url": self.url, "desc": self.desc,
            "className": self.className, "color": self.color,
            "editable": self.editable,
            "textColor": self.textColor, 
            "backgroundColor": self.backgroundColor,
            "bordercolor": self.borderColor }

class Status(db.Model):
    __tablename__ = "statuses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    label = db.Column(db.String(32))
