import os
import json
from datetime import datetime, timedelta
import sqlalchemy
import functools
import pytz
from pytz import timezone

from flask import render_template, flash, current_app, \
                    redirect, url_for, send_from_directory, send_file, \
                    request
from flask_login import login_required, current_user
from werkzeug import secure_filename
from sqlalchemy import func, or_
from sqlalchemy.orm import contains_eager, subqueryload, joinedload

from app.eboard import eboard 
from app.eboard.forms import NoteForm, TaskForm, ProjectForm, MilestoneForm
from app.models import Task, Tag, Note, Project,\
    Milestone, Event, User
from app import db
from app.models import dtformat_default


def access_required(owner_only=False):
    '''
    Decorator for restricting access to anonymouse users and logged in users
    visiting private profiles.
    '''
    def wrapper(func):
        @login_required
        @functools.wraps(func)
        def access(username, *args, **kwargs):
            try:
                user = db.session.query(User).filter_by(username=username).one()
            except sqlalchemy.orm.exc.NoResultFound:
                return render_template("404.html"), 404
            if current_user.username != username and (user.public == False or owner_only):
                return render_template("404.html"), 404 
            return func(user, *args, **kwargs)
        return access
    return wrapper



################################################################################
# Index

@eboard.route("/", methods=["GET"])
@access_required()
def eboard_root(user):
    return redirect(url_for("eboard.index", username=user.username))

@eboard.route("/<username>/", methods=["GET"])
@access_required()
def index(user):

    projects = user.projects.filter(Project.active == True).with_entities(
                   Project.name, Project.desc, Project.deadline, 
                   Project.created).order_by(
                   Project.created).all()

    notes = user.notes.order_by(Note.timestamp.asc()).limit(5).all()


    tasks = user.tasks.filter(Task.active == True, Task.complete == False).\
                order_by(Task.deadline.asc()).limit(5).\
                with_entities(Task.title, Task.deadline).all()

    deadlines = [ {"title": "Task '" + task.title + "'", 
                   "deadline": task.deadline, 
                   "daysleft": (task.deadline - datetime.now()).days,
                   "delayed": task.deadline < datetime.now() } 
                   for task in tasks ]
    deadlines.extend([ {"title": "Project '" + project.name + "'",
                        "deadline": project.deadline,
                        "daysleft": (project.deadline - datetime.now()).days,
                        "delayed": project.deadline < datetime.now() } 
                        for project in projects ])
    deadlines.sort(key = lambda x: x["deadline"])

    return render_template("eboard/index.html", user=user, projects=projects,
                           notes=notes, deadlines=deadlines)

################################################################################
# Tasks

@eboard.route("/<username>/tasks", methods=["GET"])
@access_required()
def tasks(user):
    page = int(request.args.get("page", 1))
    tasks_free = user.tasks
    tasks_pros = user.projects.join(Milestone).join(Task).with_entities(Task)
    tasks_all = tasks_free.union_all(tasks_pros)
    pagination = tasks_all.order_by(Task.complete.asc(), Task.deadline.asc()).\
                     paginate(page, per_page = 10, error_out=False)

    # Convert deadlines to user time zone
    user_tz = timezone(user.timezone)
    for task in tasks_all:
        task.deadline = pytz.utc.localize(task.deadline).\
                            astimezone(user_tz).replace(tzinfo=None)

    return render_template("eboard/tasks.html", tasks=pagination.items, 
                           pagination=pagination, user=user)

# Does not work.
@eboard.route("/<username>/tasks/<task_id>", methods=["GET"])
@access_required()
def task_show(user, task_id):
    task = user.tasks.filter(Task.id == task_id).one_or_none()
    if not task:
        return render_template("404.html"), 404
    return render_template("eboard/task.html", task=task, user=user)


@eboard.route("/<username>/tasks/new", methods=["GET", "POST"])
@access_required(owner_only=True)
def task_create(user):
    form = TaskForm(request.form)
    if form.validate_on_submit():
        data = request.form.to_dict()
        if "tags" in data:
            data["tags"] = [ tag.strip() for tag in data["tags"].split(",") ]
        task = user.add_task(timezone=timezone(user.timezone), **data)
        return redirect(url_for("eboard.tasks", username=user.username))       
    return render_template("eboard/task_edit.html", form=form, user=user)


@eboard.route("/<username>/tasks/<task_id>/edit", methods=["GET", "POST"])
@access_required(owner_only=True)
def task_edit(user, task_id):
    task = db.session.query(Task).filter(Task.id == task_id).one_or_none()
    if not task:
        return render_template("404.html"), 404       
    form = TaskForm(request.form, obj=task)
    if form.validate_on_submit():
        data = { key: value for key, value in form.data.items() 
                            if key not in ("tags",)}
        data["tags"] = [ tag.strip() for tag in form.tags.data.split(",") ]
        task.update(data, timezone=timezone(user.timezone))
        return redirect(url_for("eboard.tasks", username=user.username))

    # Adjust tags for template
    if len(task.tags) > 0:
        form.tags.data = ",".join(tag.name for tag in task.tags)

    # Adjust deadline in form to user time zone
    form.deadline.data = pytz.utc.localize(form.deadline.data).\
                             astimezone(timezone(user.timezone))
    return render_template("eboard/task_edit.html", form=form, user=user)


@eboard.route("/<username>/tasks/<task_id>/delete", methods=["DELETE", "GET"])
@access_required(owner_only=True)
def task_delete(user, task_id):
    task = db.session.query(Task).filter(Task.id == task_id).one_or_none()
    if not task:
        return render_template("404.html"), 404
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("eboard.tasks", username=user.username))

# Tasks
################################################################################

################################################################################
# Projects

@eboard.route("/<username>/projects", methods=["GET"])
@access_required(owner_only=False)
def projects(user):
    page = int(request.args.get("page", 1))
    pagination = user.projects.order_by(Project.deadline.desc()).paginate(\
        page, per_page = 10, error_out=False)
    projects_db = pagination.items

    # Convert deadlines to user time zone
    user_tz = timezone(user.timezone)
    for project in projects_db:
        project.deadline = pytz.utc.localize(project.deadline).\
                               astimezone(user_tz).replace(tzinfo=None)
        project.created = pytz.utc.localize(project.created).\
                              astimezone(user_tz).replace(tzinfo=None)

    return render_template("eboard/projects.html", pagination=pagination,
                           projects=projects_db, user=user)

@eboard.route("/<username>/projects/new", methods=["GET", "POST"])
@access_required(owner_only=True)
def project_create(user):
    form = ProjectForm(request.form)
    if form.validate_on_submit():
        data = request.form.to_dict()
        user.add_project(timezone=timezone(user.timezone), **data)
        return redirect(url_for("eboard.projects", username=user.username))        
    return render_template("eboard/project_edit.html", form=form, user=user)

@eboard.route("/<username>/projects/<project_id>", methods=["GET"])
@access_required(owner_only=False)
def project_show(user, project_id):
    project = user.projects.filter(Project.id == project_id).one_or_none()
    if not project:
        return render_template("404.html"), 404
    return render_template("eboard/project.html", project=project, user=user)

@eboard.route("/<username>/projects/<project_id>/edit", methods=["GET", "POST"])
@access_required(owner_only=True)
def project_edit(user, project_id):
    project = user.projects.filter(Project.id == project_id).one_or_none()
    if not project:
        return render_template("404.html"), 404       
    form = ProjectForm(request.form, obj=project)
    if form.validate_on_submit():
        project.update(form.data, timezone=timezone(user.timezone))
        return redirect(url_for("eboard.project_show", username=user.username,
                                project_id=project_id))

    # Adjust deadline in form to user time zone
    form.deadline.data = pytz.utc.localize(form.deadline.data).\
                             astimezone(timezone(user.timezone))

    return render_template("eboard/project_edit.html", form=form,
                           projectid=project_id, user=user)

@eboard.route("/<username>/projects/<project_id>/delete", methods=["GET", "POST"])
@access_required(owner_only=True)
def project_delete(user, project_id):
    project = user.projects.filter(Project.id == project_id).one_or_none()
    if not project:
        return render_template("404.html"), 404
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for("eboard.projects", username=user.username))


# Projects
################################################################################

################################################################################
# Notes

@eboard.route("/<username>/notes", methods=["GET"])
@access_required(owner_only=False)
def notes(user):
    page = int(request.args.get("page", 1))
    notes_free = user.notes
    notes_pros = user.projects.join(Note).with_entities(Note)
    notes_all = notes_free.union_all(notes_pros)
    pagination = notes_all.order_by(Note.timestamp.desc()).paginate(
        page, per_page = 10, error_out=False)

    user_tz = timezone(user.timezone)
    for note in notes_all:
        note.timestamp = pytz.utc.localize(note.timestamp).\
                            astimezone(user_tz).replace(tzinfo=None)

    return render_template("eboard/notes.html", pagination=pagination,
                           notes=pagination.items, user=user)

@eboard.route("/<username>/notes/new", methods=["GET", "POST"])
@access_required(owner_only=True)
def note_create(user):
    form = NoteForm(request.form)
    if form.validate_on_submit():
        data = request.form.to_dict()
        if "tags" in data:
            data["tags"] = [ tag.strip() for tag in data["tags"].split(",") ]
        note = user.add_note(**data)
        return redirect(url_for("eboard.notes", username=user.username))
    return render_template("eboard/note_edit.html", form=form, user=user)

@eboard.route("/<username>/notes/<note_id>/edit", methods=["GET", "POST"])
@access_required(owner_only=True)
def note_edit(user, note_id):
    note = db.session.query(Note).filter(Note.id == note_id).one_or_none()
    if not note:
        return render_template("404.html"), 404

    form = NoteForm(request.form, obj=note)
    if form.validate_on_submit():
        data = { key: value for key, value in form.data.items() 
                            if key not in ("tags",)}
        data["tags"] = [ tag.strip() for tag in form.tags.data.split(",") ]
        note.update(data)
        return redirect(url_for("eboard.notes", username=user.username))

    # Adjust tags for template
    if len(note.tags) > 0:
        form.tags.data = ",".join(tag.name for tag in note.tags)

    return render_template("eboard/note_edit.html", form=form, user=user)

@eboard.route("/<username>/notes/<note_id>/delete", methods=["GET", "DELETE"])
@access_required(owner_only=True)
def note_delete(user, note_id):
    note = db.session.query(Note).filter(Note.id == note_id).one_or_none()
    if not note:
        return render_template("404.html"), 404
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("eboard.notes", username=user.username)) 

# Notes
################################################################################

################################################################################
# Calendar

@eboard.route("/<username>/calendar")
@access_required(owner_only=False)
def calendar(user):
    return render_template("eboard/calendar.html", user=user)

# Calendar
################################################################################