from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import redirect, url_for
from . import db
from app.utils import merge_dicts
import datetime

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
    tags = db.relationship("Tag", secondary = taskstags)

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
                    description = "Deadline of the task is on " 
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
                           "urgency", "active", "complete"}
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
                self.deadline_event.description = \
                            "Deadline of the task is on " + \
                            self.deadline.strftime("%Y-%m-%d %H:%M:%S") + "."

        if commit:
            db.session.commit()


    def move2dict(self, extradict = {}):
        return merge_dicts({"title": self.title, 
            "created": self.created.strftime("%Y-%m-%d %H:%M:%S"),
             "deadline": self.deadline.strftime("%Y-%m-%d %H:%M:%S"),
             "notes": self.notes, 
             "tags": [ {"name": tag.name, "id": tag.id} for tag in self.tags ],
             "status": {"name": self.status.name, 
             "label": self.status.label } if self.status else None,
             "daysleft": self.daysleft, "id": self.id, 
             "importance": self.importance,
             "urgency": self.urgency }, extradict)

    @property
    def daysleft(self):
        return (self.deadline - datetime.datetime.now()).days


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    tasks = db.relationship("Task", secondary = taskstags)
    notes = db.relationship("Note", secondary = notestags)

    def move2dict(self): 
        return { "id": self.id, "name": self.name }


class Status(db.Model):
    __tablename__ = "statuses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    label = db.Column(db.String(32))


class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), unique=False)
    author = db.Column(db.String(256), unique=False)
    file_path = db.Column(db.String(256))
    description = db.Column(db.String())

    def __repr__(self):
        return "<Book '%r'>" % self.title


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

    def __repr__(self):
        return '<User %r>' % self.username


class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    title = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, 
        default=datetime.datetime.utcnow)

    tags = db.relationship("Tag", secondary = notestags)

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"));
    project = db.relationship("Project", back_populates="notes")

    def move2dict(self):
        return { "id": self.id, "title": self.title, "body": self.body,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "tags": [{"name": tag.name, "id": tag.id} for tag in self.tags ]}


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    active = db.Column(db.Boolean(), default=True)
    complete = db.Column(db.Boolean(), default=False)

    milestones = db.relationship("Milestone", back_populates="project",
        cascade = "all, delete, delete-orphan")
    notes = db.relationship("Note", back_populates="project",
        cascade = "all, delete, delete-orphan")

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
                description = "Deadline of the project is set on " + 
                    self.deadline.strftime("%Y-%m-%d %H:%M:%S") + ".",
                editable = False)


    def update(self, data=None, commit=True, **kwargs):
        '''
        Update project on the base of dict or **kwargs.
        '''
        if not data:
            data = kwargs

        # Update fields which can be update (not read-only fields)
        update_possible = {"name", "description", "deadline", 
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
                self.deadline_event.description = \
                            "Deadline of the project is on " + \
                            self.deadline.strftime("%Y-%m-%d %H:%M:%S") + "."

        if commit:
            db.session.commit()


    def move2dict(self):
        return {"id": self.id, "name": self.name, 
            "description": self.description,
            "deadline": self.deadline.strftime("%Y-%m-%d %H:%M"),
            "created": self.created.strftime("%Y-%m-%d %H:%M"),
            "modified": self.modified.strftime("%Y-%m-%d %H:%M")}


class Milestone(db.Model):
    __tablename__ = "milestones"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.Text)
    position = db.Column(db.Integer, default=0)

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    project = db.relationship("Project", back_populates="milestones")

    tasks = db.relationship("Task", back_populates="milestone",
        cascade = "all, delete, delete-orphan")

    def move2dict(self):
        return { "id": self.id, "title": self.title, 
            "description": self.description,
            "project_id": self.project_id, 
            "tasks": [ task.move2dict() for task in self.tasks ]}


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
    description = db.Column(db.String)

    # Relationships
    task = db.relationship("Task", back_populates = "deadline_event", 
        uselist = False)
    project = db.relationship("Project", back_populates = "deadline_event", 
        uselist = False)

    def move2dict(self):
        return {"id": self.id, "title": self.title, "allDay": self.allDay,
            "start": self.start.strftime("%Y-%m-%d %H:%M:%S"),
            "end": self.end.strftime("%Y-%m-%d %H:%M:%S"),
            "url": self.url, "description": self.description,
            "className": self.className, "color": self.color,
            "editable": self.editable,
            "textColor": self.textColor, 
            "backgroundColor": self.backgroundColor,
            "bordercolor": self.borderColor }