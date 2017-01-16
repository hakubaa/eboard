import os
import json
from datetime import datetime
import sqlalchemy
import functools

from flask import render_template, flash, current_app, \
                    redirect, url_for, send_from_directory, send_file, \
                    request
from flask_login import login_required, current_user
from werkzeug import secure_filename
from sqlalchemy import func
from sqlalchemy.orm import contains_eager, subqueryload, joinedload

from app.eboard import eboard 
from app.eboard.forms import UploadBookForm, NoteForm, TaskForm,\
        ProjectForm, MilestoneForm, NoteFilterForm
from app.models import Task, Tag, Status, Note, Project,\
    Milestone, Event, User
from app import db
from app.utils import merge_dicts


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
            if not owner_only and not user.public and current_user.username != username:
                return render_template("404.html"), 404 
            return func(user, *args, **kwargs)
        return access
    return wrapper


@eboard.route("/<username>/", methods=["GET"])
@access_required()
def index(user):
    return render_template("eboard/index.html")

################################################################################
# Tasks

@eboard.route("/<username>/tasks", methods=["GET"])
@access_required()
def tasks(user):
    page = int(request.args.get("page", 1))
    pagination = user.tasks.order_by(Task.deadline.desc()).paginate(\
        page, per_page = 10, error_out=False)
    return render_template("eboard/tasks.html", tasks=pagination.items, 
                           pagination=pagination, user=user)


@eboard.route("/<username>/tasks/<task_id>", methods=["GET"])
@access_required()
def task_show(user, task_id):
    task = user.tasks.filter(Task.id == task_id).one_or_none()
    if not task:
        return render_template("404.html"), 404
    return render_template("eboard/task.html", task=task)


@eboard.route("/<username>/tasks/new", methods=["GET", "POST"])
@access_required(owner_only=True)
def task_create(user):
    form = TaskForm(request.form)
    if form.validate_on_submit():
        user.add_task(title=form.title.data, deadline=form.deadline.data,
                      body=form.body.data)
        return redirect(url_for("eboard.tasks", username=user.username))       
    return render_template("eboard/task_edit.html", form=form)


@eboard.route("/<username>/tasks/<task_id>/edit", methods=["GET", "POST"])
@access_required(owner_only=True)
def task_edit(user, task_id):
    task = user.tasks.filter(Task.id == task_id).one_or_none()
    if not task:
        return render_template("404.html"), 404       
    form = TaskForm(request.form, obj=task)
    if form.validate_on_submit():
        task.update(form.data)
        return redirect(url_for("eboard.tasks", username=user.username))
    return render_template("eboard/task_edit.html", form=form)


@eboard.route("/<username>/tasks/<task_id>/delete", methods=["DELETE", "GET"])
@access_required(owner_only=True)
def task_delete(user, task_id):
    task = user.tasks.filter(Task.id == task_id).one_or_none()
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
    return render_template("eboard/projects.html", pagination=pagination,
                           projects=pagination.items, user=user)

@eboard.route("/<username>/projects/new", methods=["GET", "POST"])
@access_required(owner_only=True)
def project_create(user):
    form = ProjectForm()
    if form.validate_on_submit():
        data = request.form.to_dict()
        user.add_project(**data)
        return redirect(url_for("eboard.projects", username=user.username))        
    return render_template("eboard/project_edit.html", form=form)

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
        project.update(form.data)
        return redirect(url_for("eboard.projects", username=user.username))
    return render_template("eboard/project_edit.html", form=form)

# Projects
################################################################################

@eboard.route("/")
@login_required
def index_old():

    # projects = db.session.query(Project).join(Project.status).\
    #     filter(Status.name == "active").options(contains_eager(Project.status)).\
    #     with_entities(Project.name, Project.description, Project.deadline, 
    #         Project.created).\
    #     order_by(Project.created).all()

    # notes = db.session.query(Note).options(subqueryload(Note.tags)).\
    #     order_by(Note.timestamp.asc()).all()

    # tasks = db.session.query(Task).join(Task.status).\
    #     filter(Status.name == "active").options(contains_eager(Task.status)).\
    #     order_by(Task.deadline.asc()).limit(5).with_entities(Task.title,
    #         Task.deadline).all()
    
    # deadlines = [ {"title": "Task '" + task.title + "'", 
    #     "deadline": task.deadline, 
    #     "delayed": task.deadline < datetime.datetime.now() } for task in tasks ]
    # deadlines.extend([ {"title": "Project '" + project.name + "'",
    #     "deadline": project.deadline,
    #     "delayed": project.deadline < datetime.datetime.now() } for project in projects ])
    # deadlines.sort(key = lambda x: x["deadline"])

    projects = []
    deadlines = []
    notes = []

    return render_template("eboard/index.html", deadlines = deadlines, 
        projects = projects, notes = notes)

@eboard.route("/tasks", methods = ["GET", "POST"])
@login_required
def tasks_old():
    tasks = db.session.query(Task).outerjoin(Task.status).\
        order_by(Status.name.asc()).order_by(Task.deadline.asc()).all()
    tags = db.session.query(Tag).all()
    projects = db.session.query(Project.id, Project.name).all()
    return render_template("eboard/tasks.html", tasks = True, tags = tags, projects = projects,\
        tasksJSON = [ merge_dicts(task.move2dict(),\
            { "project": None } if not task.milestone else { "project": {\
                "id": task.milestone.project.id, "name": task.milestone.project.name } })\
            for task in tasks ])

################################################################################
# New Tag
################################################################################

@eboard.route("/tasks/newtag", methods = ["POST", "GET"])
@login_required
def new_tag():
    tag_name = request.json.get("tagname")
    if tag_name:
        tag = db.session.query(Tag).filter(func.lower(Tag.name) == func.lower(tag_name)).first()
        if not tag:
            tag = Tag(name = tag_name)
            db.session.add(tag)
            db.session.commit()
        return json.dumps({ "status": "success", "data": tag.move2dict()}), 200
    return json.dumps({"status": "failure", "data": {"info": "No tag name."}}), 200

################################################################################
# Tasks Bookmark
################################################################################

@eboard.route("/tasks/get", methods = ["POST"])
@login_required
def send_task():
    task_id = int(request.form.get("taskid"));
    if task_id:
        task = db.session.query(Task).filter(Task.id == task_id).first()
        if task:
            return json.dumps({
                    "title": task.title,
                    "notes": task.notes,
                    "tags": [ { "name": tag.name, "id": tag.id } for tag in task.tags ],
                    "deadline": str(task.deadline),
                    "status": task.status.label
                }), 200
    return "", 500


@eboard.route("/tasks/remove", methods=["POST"])
@login_required
def remove_task():
    task_id = request.json.get("taskid")
    task = Task.query.filter(Task.id == int(task_id)).one_or_none()
    if task:
        db.session.delete(task)
        db.session.commit();
        return json.dumps({"status": "success", 
            "data": { "taskid": task_id }}), 200  
    return json.dumps({"status": "failure", 
        "data": {"info": "Lack of task record"}}), 200


@eboard.route("/tasks/edit/", defaults={"taskid": None}, methods=["GET", "POST"])
@eboard.route("/tasks/edit/<int:taskid>", methods=["GET", "POST"])
@login_required
def edit_task(taskid):
    form = TaskForm()
    if form.validate_on_submit():
        tags = []
        if form.tags.data:
            tags = [ int(tag) for tag in json.loads(form.tags.data) if tag.isdigit() ]
        if taskid:
            task = db.session.query(Task).options(joinedload(Task.deadline_event)).\
                filter(Task.id == taskid).one()
            task.title = form.title.data
            task.deadline = form.deadline.data
            task.notes = form.notes.data
            task.tags = Tag.query.filter(Task.id.in_(tags)).all()
            if task.deadline_event:
                task.deadline_event.end = task.deadline
                task.deadline_event.start = task.deadline - datetime.timedelta(minutes=30)
            flash("The task '%s' has been updated." % task.title)
        else:
            task = Task(title = form.title.data, deadline = form.deadline.data,\
                notes = form.notes.data)
            task.status = Status.query.filter(Status.name == "active").first()
            task.tags = Tag.query.filter(Tag.id.in_(tags)).all()
            task.deadline_event = Event(
                title = "Task '" + task.title + ",", 
                start = task.deadline - datetime.timedelta(minutes=30),
                end = task.deadline,
                className = "fc-task-deadline",
                description = "Deadline of the task is on " + 
                    task.deadline.strftime("%Y-%m-%d %H:%M:%S") + ".",
                editable = False)
            flash("The task '%s' has been added to your taks' list. Good luck with the deadline." % task.title)

        db.session.add(task)
        db.session.commit()

        tasks = Task.query.join(Task.status).order_by(Status.name.asc()).order_by(Task.deadline.asc()).all()
        return redirect(url_for("eboard.tasks"))

    tags = [ tag.move2dict() for tag in Tag.query.all() ]

    task = None
    if taskid:
        task = db.session.query(Task).options(subqueryload(Task.tags)).\
            filter(Task.id == taskid).one_or_none()
        if task is None:
            return render_template("404.html"), 404
        form.title.data = task.title
        form.notes.data = task.notes
        form.deadline.data = task.deadline

    return render_template('eboard/edittask.html', form=form,\
        taskid = taskid, tags = tags,\
        task_tags = [] if not task else [ tag.move2dict() for tag in task.tags ])

################################################################################
# Notes Bookmark
################################################################################

@eboard.route("/notes", methods=["POST", "GET"])
@login_required
def notes():
    tags = db.session.query(Tag.id, Tag.name).all()
    projects = db.session.query(Project.id, Project.name).all()
    form = NoteFilterForm(tags, projects)
    if form.validate_on_submit():
        if form.tag.data == "all":
            if form.project.data == "all":
                query = Note.query.options(joinedload(Note.tags))
            elif form.project.data == "unbound":
                query = Note.query.options(joinedload(Note.tags)).\
                    filter(Note.project_id == None)
            else:
                query = Note.query.options(joinedload(Note.tags)).\
                    filter(Note.project_id == form.project.data)
        else:
            if form.project.data == "all":
                query = Note.query.join(Note.tags).\
                    filter(Note.tags.any(Tag.id == form.tag.data)).\
                    options(contains_eager(Note.tags))
            elif form.project.data == "unbound":
                query = Note.query.join(Note.tags).\
                    filter(Note.tags.any(Tag.id == form.tag.data)).\
                    filter(Note.project_id == None).\
                    options(contains_eager(Note.tags))
            else:
                query = Note.query.join(Note.tags).\
                    filter(Note.tags.any(Tag.id == form.tag.data)).\
                    filter(Note.project_id == form.project.data).\
                    options(contains_eager(Note.tags))

        page = 1 # restart page
    else:
        query = Note.query.options(joinedload("tags"))
        page = request.args.get("page", 1, type=int)

    pagination = query.order_by(Note.timestamp.desc()).paginate(\
        page, per_page = 10, error_out=False)
    notes = pagination.items

    # Add project_name to each note ascribed to a project
    projects_dict = { project.id: project.name for project in projects }
    for note in notes:
        if note.project_id:
            note.project_name = projects_dict[note.project_id]

    return render_template("eboard/notes.html", form = form, notes = notes,\
        pagination = pagination)


@eboard.route("/notes/edit/", defaults={"noteid": None}, methods=["GET", "POST"])
@eboard.route('/notes/edit/<int:noteid>', methods=['GET', 'POST'])
@login_required
def editnote(noteid):
    form = NoteForm()
    if form.validate_on_submit():
        tags = []
        if form.tags.data:
            tags = [ int(tag) for tag in json.loads(form.tags.data) if tag.isdigit() ]

        if noteid:
            note = Note.query.get_or_404(noteid)
            note.title = form.title.data
            note.tags = Tag.query.filter(Tag.id.in_(tags)).all()
            note.body = form.body.data
            flash("The note '%s' has been updated." % note.title)
        else:
            note = Note(title = form.title.data, body = form.body.data,\
                tags = Tag.query.filter(Tag.id.in_(tags)).all())
            flash("The note '%s' has been created." % note.title)

        db.session.add(note)
        db.session.commit()

        notes = Note.query.order_by(Note.timestamp.asc()).all()
        return redirect(url_for("eboard.notes"))

    tags = [ tag.move2dict() for tag in Tag.query.all() ]

    note = None
    if noteid:
        note = Note.query.get_or_404(noteid)
        form.title.data = note.title
        form.body.data = note.body

    return render_template('eboard/editnote.html', form=form,\
        noteid = noteid, tags = tags, note_tags = [] if not note else\
        [ tag.move2dict() for tag in note.tags ])

@eboard.route("/notes/remove/<int:noteid>", methods=["GET", "POST"])
@login_required
def removenote(noteid):
    note = Note.query.get_or_404(noteid)
    db.session.delete(note)
    db.session.commit()
    flash("The note '%s' has been removed." % note.title)
    return redirect(url_for("eboard.notes"))

################################################################################
# Project Bookmark
################################################################################

@eboard.route("/projects", methods=["GET", "POST"])
@login_required
def projects_2():
    projects = db.session.query(Project.id, Project.name, Project.description,\
        Project.created, Project.deadline).\
        order_by(Project.created.asc()).all()
    return render_template("eboard/projects/index.html", projects = projects)

@eboard.route("/project/<int:projectid>", methods=["GET", "POST"])
@login_required
def project_2(projectid):
    project = None
    projects = None
    tags = None

    if projectid:
        project = db.session.query(Project).options(subqueryload("milestones").\
            joinedload("tasks").joinedload("status")).options(
            subqueryload("milestones").joinedload("tasks").joinedload("tags")).\
            options(joinedload("notes")).filter(Project.id == projectid).one()

        project.tasks2do = [task for milestone in project.milestones\
            for task in milestone.tasks if task.status.name == "active" ]
        project.tasks2do.sort(key = lambda task: task.deadline)
        project.tasks2do = project.tasks2do[:5]

        if datetime.datetime.now() > project.deadline:
            project.progress = 100
        elif project.created > datetime.datetime.now():
            project.progress = 0
        elif project.deadline <= project.created:
            project.progress = 100
        else:
            project.progress = round(100*\
                (datetime.datetime.now() - project.created).total_seconds()/\
                (project.deadline - project.created).total_seconds(), 0)

        tags = [ tag.move2dict() for tag in Tag.query.all() ]   
    else:
        projects = db.session.query(Project.name, Project.description,\
            Project.created, Project.deadline).\
            order_by(Project.created.asc()).all()

    return render_template("eboard/projects/project.html",\
        projects = projects, project = project, tags = tags)

@eboard.route("/project/new", methods=["GET", "POST"])
@login_required
def project_new():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(name = form.name.data, deadline = form.deadline.data,
            description = form.description.data, 
            status = Status.query.filter(Status.name == "active").one())
        project.deadline_event = Event(
            title = "Project '" + project.name + ",", 
            start = project.deadline - datetime.timedelta(minutes=30),
            end = project.deadline,
            className = "fc-project-deadline",
            description = "Deadline of the project is set on " + 
                project.deadline.strftime("%Y-%m-%d %H:%M:%S") + ".",
            editable = False)
        db.session.add(project)
        db.session.commit()
        # projects = Project.query.order_by(Project.created.asc()).all()
        flash("The project '%s' has been created." % project.name)
        return redirect(url_for("eboard.projects"))

    return render_template('eboard/projects/newproject.html', form=form)

@eboard.route("/project/remove/<int:projectid>", methods=["GET", "POST"])
@login_required
def project_remove(projectid):
    project = Project.query.get_or_404(projectid)
    if project:
        db.session.delete(project)
        db.session.commit()
    return redirect(url_for("eboard.projects"))

@eboard.route("/project/get", methods=["POST", "GET"])
@login_required
def project_get():
    project_id = request.json.get("id")
    project = db.session.query(Project).options(subqueryload("milestones").\
        joinedload("tasks").joinedload("status")).options(
        subqueryload("milestones").joinedload("tasks").joinedload("tags")).\
        options(joinedload("notes")).filter(Project.id == int(project_id)).one()

    if project:
        tasks2do = [task for milestone in project.milestones\
            for task in milestone.tasks if task.status.name == "active" ]
        tasks2do.sort(key = lambda task: task.deadline)
        tasks2do = tasks2do[:5]
        return json.dumps({"status": "success", "data": merge_dicts(
            project.move2dict(), 
            {"tasks2do": [task.move2dict() for task in tasks2do]}) }), 200  

    return json.dumps({"status": "failure", "data": {"info": "Lack of project record."}})

@eboard.route("/project/edit", methods=["POST", "GET"])
@login_required
def project_edit_old():
    project_id = request.json.get("id")
    project = db.session.query(Project).options(joinedload(Project.deadline_event)).\
        filter(Project.id == int(project_id)).one_or_none();
    if project:
        project.name = request.json.get("name")
        project.description = request.json.get("description")
        project.deadline = datetime.datetime.strptime(request.json.get("deadline"), "%Y-%m-%d %H:%M")
        project.modified = datetime.datetime.utcnow()
        if project.deadline_event is not None:
            project.deadline_event.end = project.deadline
            project.deadline_event.start = project.deadline - datetime.timedelta(minutes=30)
        db.session.commit()
        return json.dumps({"status": "success", "data": project.move2dict()}), 200  
    else:
        return json.dumps({"status": "failure", "data": {"info": "No given project."}}), 200

################################################################################
# Milestones
################################################################################

@eboard.route("/project/milestone/get", methods=["POST", "GET"])
@login_required
def milestone_get():
    milestone_id = request.json.get("milestoneid")
    milestone = db.session.query(Milestone).options(subqueryload("tasks").\
        joinedload("status")).options(subqueryload("tasks").joinedload("tags")).\
        filter(Milestone.id == int(milestone_id)).one_or_none()
    if milestone:
        return json.dumps({"status": "success", "data": milestone.move2dict()}), 200  
    return json.dumps({"status": "failure", "data": {"info": "No milestone record"}}), 200

@eboard.route("/project/milestone/edit", methods=["POST", "GET"])
@login_required
def milestone_edit():
    milestone_id = request.json.get("id")
    if milestone_id: #update
        milestone = Milestone.query.\
            filter(Milestone.id == int(milestone_id)).one_or_none()
        if not milestone:
            return json.dumps({"status": "failure", "data": {"info": "Lack of milestone record."}}), 200
        milestone.title = request.json.get("title")
        milestone.description = request.json.get("description")
    else: #new
        project = Project.query.filter(Project.id == int(request.json.get("projectid"))).first()
        max_pos = db.session.query(func.max(Milestone.position)).filter(Milestone.project == project).first()[0]
        if max_pos is None:
            max_pos = 0
        else:
            max_pos = max_pos + 1
        milestone = Milestone(title = request.json.get("title"),\
            description = request.json.get("description"),\
            position = max_pos)
        db.session.add(milestone)
        if not project:
            return json.dumps({"status": "failure", "data": {"info": "Lack of project record."}}), 200
        project.milestones.append(milestone)
    db.session.commit()
    return json.dumps({"status": "success", "data": {"id": milestone.id, "title": milestone.title}}), 200  

@eboard.route("/project/milestone/move", methods=["POST", "GET"])
@login_required
def milestone_move():
    milestone_id = int(request.json.get("milestoneid"))
    milestone = Milestone.query.filter(Milestone.id == milestone_id).one_or_none()
    if milestone:
        direction = int(request.json.get("direction"))
        if direction == 1: # move up
            milestone_other = Milestone.query.filter(Milestone.position < milestone.position).\
                filter(Milestone.project == milestone.project).\
                order_by(Milestone.position.desc()).one_or_none()
        elif direction == -1: # move down
            milestone_other = Milestone.query.filter(Milestone.position > milestone.position).\
                filter(Milestone.project == milestone.project).\
                order_by(Milestone.position.asc()).one_or_none()
        else: # what the fuck
            return json.dumps({"status": "failure", "data":{"info": "Invalid input"}}), 200
        if milestone_other:
            temp = milestone.position
            milestone.position = milestone_other.position
            milestone_other.position = temp
            db.session.commit() 
            return json.dumps({ "id": milestone.id}), 200
        return json.dumps({"status": "success", "data": { "id": None}}), 200
    return json.dumps({"status": "failure", "data":{"info": "No milestone record"}}), 200

@eboard.route("/project/milestone/remove", methods=["POST", "GET"])
@login_required
def milestone_remove():
    milestone_id = int(request.json.get("milestoneid"))
    milestone = Milestone.query.filter(Milestone.id == milestone_id).one()
    db.session.delete(milestone)
    db.session.commit()
    return json.dumps({"status": "success", "data": {"id": milestone_id}}), 200

@eboard.route("/project/milestone/list4task", methods=["POST", "GET"])
@login_required
def milestone_list4task():
    task_id = request.json.get("taskid")
    if task_id:
        task = Task.query.filter(Task.id == int(task_id)).one_or_none()
        milestones = { milestone.id: milestone.title for milestone in \
            task.milestone.project.milestones }
        return json.dumps({"status": "success", "milestones": milestones}), 200
    return json.dumps({"status": "failure"}), 500

################################################################################
# Tasks
################################################################################

@eboard.route("/project/task/edit", methods=["POST", "GET"])
@login_required
def task_edit_old():
    task_id = request.json.get("id")
    tags = [ int(tag) for tag in json.loads(request.json.get("tags")) if tag.isdigit() ]
    if task_id: #update
        task = db.session.query(Task).options(joinedload(Task.deadline_event)).\
            filter(Task.id == int(task_id)).one_or_none()
        if not task:
            return json.dumps({"status": "failure", "data": {"info": "No given task."}}), 200
        task.title = request.json.get("title")
        task.notes = request.json.get("notes")
        task.deadline = datetime.datetime.strptime(request.json.get("deadline"), "%Y-%m-%d %H:%M")
        task.tags = Tag.query.filter(Tag.id.in_(tags)).all()
        if task.deadline_event:
            task.deadline_event.end = task.deadline
            task.deadline_event.start = task.deadline - datetime.timedelta(minutes=30)
    else: #new
        milestone = Milestone.query.filter(Milestone.id == int(request.json.get("milestoneid"))).one_or_none()
        if not milestone:
            return json.dumps({"status": "failure", "data": {"info": "No given milestone."}}), 200
        task = Task(title = request.json.get("title"),\
            notes = request.json.get("notes"),\
            deadline = datetime.datetime.strptime(request.json.get("deadline"), "%Y-%m-%d %H:%M"),
            status = Status.query.filter(Status.name == "active").one(),
            tags = Tag.query.filter(Tag.id.in_(tags)).all())
        task.deadline_event = Event(
            title = "Task '" + task.title + ",", 
            start = task.deadline - datetime.timedelta(minutes=30),
            end = task.deadline,
            className = "fc-task-deadline",
            description = "Deadline of the task is on " + 
                task.deadline.strftime("%Y-%m-%d %H:%M:%S") + ".",
            editable = False)
        db.session.add(task)
        milestone.tasks.append(task)
    db.session.commit()
    return json.dumps({"status": "success", "data": {"id": task.id, "title": task.title, "deadline": \
        task.deadline.strftime("%Y-%m-%d %H:%M")}}), 200  

@eboard.route("/project/task/get", methods=["POST", "GET"])
@login_required
def task_get():
    task_id = request.json.get("taskid")
    if task_id:
        task = Task.query.filter(Task.id == int(task_id)).one_or_none()
        if task:
            return json.dumps({ "status": "success", "data": task.move2dict()}), 200  
    return json.dumps({"status": "failure", "data": {"info": "No task record"}}), 200

@eboard.route("/project/task/remove", methods=["POST", "GET"])
@login_required
def task_remove():
    print("Delete task")
    task_id = request.json.get("taskid")
    task = Task.query.filter(Task.id == int(task_id)).one_or_none()
    if task:
        milestone_id = task.milestone_id
        db.session.delete(task)
        db.session.commit()
        return json.dumps({"status": "success", "data": {"id": task_id, "milestoneid": milestone_id}}), 200  
    return json.dumps({"status": "failure", "data": {"info": "No task record"}}), 200

@eboard.route("/project/task/status", methods=["POST", "GET"])
@login_required
def task_status():
    task_id = request.json.get("taskid")
    status = db.session.query(Status).\
        filter(Status.name == request.json.get("status")).one()
    db.session.query(Task).filter(Task.id == int(task_id)).\
        update({"status_id": status.id})
    db.session.commit()
    return json.dumps({"status": "success", "data": 
        {"id": task_id, "status": status.name}}), 200  

@eboard.route("/project/task/move", methods=["POST", "GET"])
@login_required
def task_move():
    task_id = request.json.get("taskid")
    task = Task.query.filter(Task.id == int(task_id)).one()
    if task:
        milestone_id = request.json.get("milestoneid")
        if db.session.query(db.session.query(Milestone).\
                filter(Milestone.id == int(milestone_id)).exists()).scalar():
            task.milestone_id = milestone_id
            db.session.commit()
            return json.dumps({"status": "success", "id": task_id, "milestoneid": milestone_id}), 200
        return json.dumps({"status": "failure", "data": {"info": "Lack of milestone record."}}), 200 
    return json.dumps({"status": "failure", "data": {"info": "Lack of task record."}}), 200

################################################################################
# Notes
################################################################################

@eboard.route("/project/note/edit", methods=["POST", "GET"])
@login_required
def note_edit():
    note_id = request.json.get("id")
    tags = [ int(tag) for tag in json.loads(request.json.get("tags")) if tag.isdigit() ]
    if note_id: #update
        note = Note.query.filter(Note.id == int(note_id)).one_or_none()
        if not note:
            return json.dumps({"status": "failure", "data": {"info": "Lack of note record."}}), 200
        note.title = request.json.get("title")
        note.body = request.json.get("body")
        note.tags = Tag.query.filter(Tag.id.in_(tags)).all()
    else: #new
        project = Project.query.filter(Project.id == int(request.json.get("projectid"))).one_or_none()
        if not project:
            return json.dumps({"status": "failure", "data": {"info": "Lack of project record."}}), 200
        note = Note(title = request.json.get("title"), body = request.json.get("body"),\
            tags = Tag.query.filter(Tag.id.in_(tags)).all())
        db.session.add(note)
        project.notes.append(note)
    db.session.commit()
    return json.dumps({"status": "success", "data": note.move2dict()}), 200  

@eboard.route("/project/note/remove", methods=["GET", "POST"])
@login_required
def note_remove():
    note_id = request.json.get("id")
    if note_id:
        Note.query.filter(Note.id == int(note_id)).delete()
        db.session.commit()
        return json.dumps({"status": "success"}), 200
    return json.dumps({"status": "failure"}), 200

@eboard.route("/project/note/get", methods=["POST", "GET"])
@login_required
def note_get():
    note_id = request.json.get("id")
    if note_id:
        note = Note.query.options(subqueryload(Note.tags)).\
            filter(Note.id == int(note_id)).one_or_none()
        if note:
            return json.dumps({"status":"success", "data": note.move2dict()}), 200  
    return json.dumps({"status": "failure", "data": 
        {"info": "Lack of note recrod."}}), 200



#
################################################################################