from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import redirect, url_for
from . import db
from . import login_manager
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
    notes = db.Column(db.String())
    importance = db.Column(db.Integer)
    urgency = db.Column(db.Integer)

    tags = db.relationship("Tag", secondary = taskstags)

    milestone_id = db.Column(db.Integer, db.ForeignKey("milestones.id"))
    milestone = db.relationship("Milestone", back_populates = "tasks")

    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'))
    status = db.relationship("Status", back_populates = "tasks")

    deadline_event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    deadline_event = db.relationship("Event", back_populates = "task",
        cascade = "all, delete, delete-orphan", single_parent = True)

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

    tasks = db.relationship("Task", back_populates = "status")
    projects = db.relationship("Project", back_populates = "status")
        

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), unique=False)
    author = db.Column(db.String(256), unique=False)
    file_path = db.Column(db.String(256))
    description = db.Column(db.String())

    def __repr__(self):
        return "<Book '%r'>" % self.title


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

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

    milestones = db.relationship("Milestone", back_populates="project",
        cascade = "all, delete, delete-orphan")
    notes = db.relationship("Note", back_populates="project",
        cascade = "all, delete, delete-orphan")

    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'))
    status = db.relationship("Status", back_populates = "projects")

    deadline_event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    deadline_event = db.relationship("Event", back_populates = "project",
        cascade = "all, delete, delete-orphan", single_parent = True)

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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("auth.login"))