import functools
from datetime import datetime

from flask import jsonify, request, Response, url_for, render_template
from flask_login import current_user, login_required
import sqlalchemy

from app import login_manager, db
from app.api import api
from app.models import User, Task, Note, Project, Milestone, Tag, Event


# Read This
# http://michal.karzynski.pl/blog/2016/06/19/
# building-beautiful-restful-apis-using-flask-swagger-ui-flask-restplus/


# Create decorator for access restriction
def access_validator(owner_auth=True):
    '''
    Decorator for restricting access to anonymouse users and logged in users
    visiting private profiles.
    '''
    def wrapper(func):
        @functools.wraps(func)
        def access(username, *args, **kwargs):
            if not current_user.is_authenticated:
                return "", 401
            try:
                user = db.session.query(User).filter_by(username=username).one()
            except sqlalchemy.orm.exc.NoResultFound:
                return "", 404
            if not owner_auth and not user.public \
               and current_user.username != username:
                return "", 404 
            return func(user, *args, **kwargs)
        return access
    return wrapper


################################################################################
# USER

@api.route("/users/<username>", methods=["GET"])
@access_validator(owner_auth=False)
def user_index(user):
    rrepr = user.to_dict()
    for task in rrepr["tasks"]:
        task["uri"] = url_for("api.task_get", username=user.username,
                              task_id=task["id"])
    for project in rrepr["projects"]:
        project["uri"] = url_for("api.project_get", username=user.username,
                                 project_id=project["id"])
    for note in rrepr["notes"]:
        note["uri"] = url_for("api.note_get", username=user.username,
                              note_id=note["id"]) 
    return jsonify(rrepr), 200

@api.route("/users/<username>", methods=["PUT"])
@access_validator(owner_auth=True)
def user_edit(user):
    mod_flag = False
    data = request.form.to_dict()
    if "public" in data:
        if data["public"].upper() in ("T", "TRUE", "YES", "Y"):
            user.public = True
            mod_flag = True
    if "new_password" in data and "new_password2" in data:
        if data["new_password"] == data["new_password2"]:
            user.password = data["new_password"]
            mod_flag = True
    if mod_flag:
        db.session.commit()
    return "", 204

@api.route("/users", methods=["POST"])
def user_create():
    data = request.form.to_dict()
    if not "username" in data:
        return "No username.", 400
    if not "password" in data or not "password2" in data:
        return "No passward or password confirmation.", 400
    if data["password"] != data["password2"]:
        return "Invalid password confirmation.", 400

    user = User(username=data["username"], password=data["password"])
    db.session.add(user)
    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        return "Username already exists.", 409

    response = Response("")
    response.status_code = 201
    response.headers["Location"] = url_for("api.user_index",
                                           username=user.username)
    return response

@api.route("/users/<username>", methods=["DELETE"])
@access_validator(owner_auth=True)
def user_delete(user):
    if user.verify_password(request.form["password"]):
        db.session.delete(user)
        db.session.commit()
        return "", 410
    return "", 400

################################################################################

################################################################################
# TASKS

@api.route("/users/<username>/tasks", methods=["GET"])
@access_validator(owner_auth=False)
def tasks(user):
    data = [ task.get_info() for task in user.tasks.all() ]
    for task in data:
        task["uri"] = url_for("api.task_get", username=user.username,
                              task_id=task["id"]) 
    return jsonify(data), 200

@api.route("/users/<username>/tasks", methods=["POST"])
@access_validator()
def task_create(user):
    data = request.form.to_dict()
    # Two fields are required
    if not "title" in data or not "deadline" in data:
        return "", 400

    try:
        task = user.add_task(**data)
    except sqlalchemy.exc.StatementError:
        db.ssession.rollback()
        return "", 400

    response = Response("")
    response.status_code = 201
    response.headers["Location"] = url_for("api.task_get", task_id=task.id,
                                           username=user.username)
    return response

@api.route("/users/<username>/tasks/<task_id>", methods=["GET"])
@access_validator(owner_auth=False)
def task_get(user, task_id):
    task = db.session.query(Task).join(User).filter(
                User.id == user.id, Task.id == task_id).first()
    if not task:
        # Look for task in user's projects
        task = user.projects.join(Milestone).join(Task).with_entities(Task).\
                   filter(Task.id == task_id).one_or_none()
        if not task:
            return "", 404
    return jsonify(task.to_dict()), 200

@api.route("/users/<username>/tasks/<task_id>", methods=["PUT"])
@access_validator(owner_auth=True)
def task_edit(user, task_id):
    task = db.session.query(Task).join(User).filter(
                User.id == user.id, Task.id == task_id).first()
    if not task:
        # Look for task in user's projects
        task = user.projects.join(Milestone).join(Task).with_entities(Task).\
                   filter(Task.id == task_id).one_or_none()
        if not task:
            return "", 404

    data = request.form.to_dict()
    try:
        task.update(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 404

    return "", 204

@api.route("/users/<username>/tasks/<task_id>", methods=["DELETE"])
@access_validator(owner_auth=True)
def task_delete(user, task_id):
    task = db.session.query(Task).join(User).filter(
                User.id == user.id, Task.id == task_id).first()
    if not task:
        # Look for task in user's projects
        task = user.projects.join(Milestone).join(Task).with_entities(Task).\
                   filter(Task.id == task_id).one_or_none()
        if not task:
            return "", 404

    db.session.delete(task)
    db.session.commit()
    return "", 204

################################################################################

################################################################################
# NOTES

@api.route("/users/<username>/notes", methods=["GET"])
@access_validator(owner_auth=False)
def notes(user):
    data = [ note.to_dict() for note in user.notes.all() ]
    for note in data:
        note["uri"] = url_for("api.note_get", username=user.username,
                              note_id=note["id"])
    return jsonify(data), 200

@api.route("/users/<username>/notes", methods=["POST"])
@access_validator(owner_auth=True)
def note_create(user):
    data = request.form.to_dict()
    # Title is required
    if "title" not in data:
        return "", 400

    try:
        note = user.add_note(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400

    response = Response("")
    response.status_code = 201
    response.headers["Location"] = url_for("api.note_get", note_id=note.id,
                                           username=user.username)
    return response

@api.route("/users/<username>/notes/<note_id>", methods=["GET"])
@access_validator(owner_auth=False)
def note_get(user, note_id):
    note = db.session.query(Note).join(User).filter(User.id == user.id,
                Note.id == note_id).first()
    if not note:
        # Look for note in user's projects
        note = user.projects.join(Note).with_entities(Note).\
                   filter(Note.id == note_id).one_or_none()
        if not note:
            return "", 404
    return jsonify(note.to_dict()), 200

@api.route("/users/<username>/notes/<note_id>", methods=["PUT"])
@access_validator(owner_auth=False)
def note_edit(user, note_id):
    note = db.session.query(Note).join(User).filter(User.id == user.id,
                Note.id == note_id).first()
    if not note:
        # Look for note in user's projects
        note = user.projects.join(Note).with_entities(Note).\
                   filter(Note.id == note_id).one_or_none()
        if not note:
            return "", 404

    data = request.form.to_dict()
    try:
        note.update(**data)
    except sqlalchemy.exc.StatementError:
        return "", 400

    return "", 204

@api.route("/users/<username>/notes/<note_id>", methods=["DELETE"])
@access_validator(owner_auth=True)
def note_delete(user, note_id):
    note = db.session.query(Note).join(User).filter(User.id == user.id,
                Note.id == note_id).first()
    if not note:
        # Look for note in user's projects
        note = user.projects.join(Note).with_entities(Note).\
                   filter(Note.id == note_id).one_or_none()
        if not note:
            return "", 404
    db.session.delete(note)
    db.session.commit()
    return "", 204


################################################################################
# PROJECTS

@api.route("/users/<username>/projects", methods=["GET"])
@access_validator(owner_auth=False)
def projects(user):
    data = [ project.get_info() for project in user.projects.all() ]
    for project in data:
        project["uri"] = url_for("api.project_get", username=user.username,
                                 project_id=project["id"])
    return jsonify(data), 200

@api.route("/users/<username>/projects", methods=["POST"])
@access_validator(owner_auth=True)
def project_create(user):
    data = request.form.to_dict()
    if "name" not in data:
        return "", 400

    try:
        project = user.add_project(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400

    response = Response("")
    response.status_code = 201
    response.headers["Location"] = url_for("api.project_get", 
                                           username=user.username,
                                           project_id=project.id)
    return response

@api.route("/users/<username>/projects/<project_id>", methods=["GET"])
@access_validator(owner_auth=False)
def project_get(user, project_id):
    # Optimize to load milestones at the same time
    project = db.session.query(Project).join(User).filter(User.id == user.id,
                    Project.id == project_id).first()
    if not project:
        return "", 404

    with_tasks = request.values.get("with_tasks", "N").upper() in ("TRUE", "T", 
                                                                   "YES", "Y")

    data = project.to_dict(with_tasks=with_tasks)
    for milestone in data["milestones"]:
        milestone["uri"] = url_for("api.milestone_get", username=user.username,
                                   project_id=project_id, 
                                   milestone_id=milestone["id"])
    return jsonify(data), 200

@api.route("/users/<username>/projects/<project_id>", methods=["PUT"])
@access_validator(owner_auth=True)
def project_edit(user, project_id):
    project = db.session.query(Project).join(User).filter(User.id == user.id,
                    Project.id == project_id).first()
    if not project:
        return "", 404
    data = request.form.to_dict()
    try:
        project.update(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400
    return "", 204

@api.route("/users/<username>/projects/<project_id>", methods=["DELETE"])
@access_validator(owner_auth=True)
def project_delete(user, project_id):
    project = db.session.query(Project).join(User).filter(User.id == user.id,
                    Project.id == project_id).first()
    if not project:
        return "", 404
    db.session.delete(project)
    db.session.commit()
    return "", 204

################################################################################

################################################################################
# PROJECT - NOTES

@api.route("/users/<username>/projects/<project_id>/notes", methods=["GET"])
@access_validator(owner_auth=False)
def project_notes(user, project_id):
    project = db.session.query(Project).join(User).filter(User.id == user.id,
                    Project.id == project_id).first()
    if not project:
        return "", 404
    data = [ note.get_info() for note in project.notes ]
    for note in data:
        note["uri"] = url_for("api.project_note_get", username=user.username,
                              project_id=project.id, note_id=note["id"])
    return jsonify(data), 200    

@api.route("/users/<username>/projects/<project_id>/notes", methods=["POST"])
@access_validator(owner_auth=True)
def project_note_create(user, project_id):
    data = request.form.to_dict()
    if "title" not in data:
        return "", 400
    project = db.session.query(Project).join(User).filter(User.id == user.id,
                    Project.id == project_id).first()
    if not project:
        return "", 404

    try:
        note = project.add_note(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400

    response = Response("")
    response.status_code = 201
    response.headers["Location"] = url_for("api.project_note_get", 
                                           username=user.username,
                                           project_id=project.id, 
                                           note_id=note.id)
    return response

@api.route("/users/<username>/projects/<project_id>/notes/<note_id>",
           methods=["GET"])
@access_validator(owner_auth=False)
def project_note_get(user, project_id, note_id):
    note = db.session.query(Note).join(Project).join(User).filter(
                User.id == user.id, Project.id == project_id,
                Note.id == note_id).first()
    if not note:
        return "", 404
    return jsonify(note.to_dict()), 200

@api.route("/users/<username>/projects/<project_id>/notes/<note_id>",
           methods=["PUT"])
@access_validator(owner_auth=True)
def project_note_edit(user, project_id, note_id):
    note = db.session.query(Note).join(Project).join(User).filter(
                User.id == user.id, Project.id == project_id,
                Note.id == note_id).first()
    if not note:
        return "", 404
    data = request.form.to_dict()

    try:
        note.update(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400

    return "", 204

@api.route("/users/<username>/projects/<project_id>/notes/<note_id>",
           methods=["DELETE"])
@access_validator(owner_auth=True)
def project_note_delete(user, project_id, note_id):
    note = db.session.query(Note).join(Project).join(User).filter(
                User.id == user.id, Project.id == project_id,
                Note.id == note_id).first()
    if not note:
        return "", 404
    db.session.delete(note)
    db.session.commit()   
    return "", 204

################################################################################

################################################################################
# PROJECT - MILESTONES

@api.route("/users/<username>/projects/<project_id>/milestones", 
           methods=["GET"])
@access_validator(owner_auth=False)
def milestones(user, project_id):
    project = db.session.query(Project).join(User).filter(User.id == user.id,
                  Project.id == project_id).one_or_none()
    if not project:
        return "", 404
    data = [ milestone.get_info() for milestone in project.milestones ]
    for milestone in data:
        milestone["uri"] = url_for("api.milestone_get", username=user.username,
                                   project_id=project.id,
                                   milestone_id=milestone["id"])
    return jsonify(data), 200

@api.route("/users/<username>/projects/<project_id>/milestones",
           methods=["POST"])
@access_validator(owner_auth=True)
def milestone_create(user, project_id):
    project = db.session.query(Project).join(User).filter(User.id == user.id, 
                   Project.id == project_id).one_or_none()
    if not project:
        return "", 404
   
    data = request.form.to_dict()
    if "title" not in data:
        return "", 400

    try:
        milestone = project.add_milestone(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400
    
    response = Response("")
    response.status_code = 201
    response.headers["Location"] = url_for("api.milestone_get", 
                                           username=user.username,
                                           project_id=project.id,
                                           milestone_id=milestone.id)
    return response

@api.route("/users/<username>/projects/<project_id>/milestones/<milestone_id>",
           methods=["GET"])
@access_validator(owner_auth=True)
def milestone_get(user, project_id, milestone_id):
    milestone = db.session.query(Milestone).join(Project).join(User).filter(
                    User.id == user.id, Project.id == project_id,
                    Milestone.id == milestone_id).first()
    if not milestone:
        return "", 404
    data = milestone.to_dict()
    for task in data["tasks"]:
        task["uri"] = url_for("api.milestone_task_get", username=user.username,
                              project_id=project_id, milestone_id=milestone_id,
                              task_id=task["id"])
    return jsonify(data), 200

@api.route("/users/<username>/projects/<project_id>/milestones/<milestone_id>",
           methods=["PUT"])
@access_validator(owner_auth=True)
def milestone_edit(user, project_id, milestone_id):
    milestone = db.session.query(Milestone).join(Project).join(User).filter(
                    User.id == user.id, Project.id == project_id,
                    Milestone.id == milestone_id).first()
    if not milestone:
        return "", 404
    data = request.form.to_dict()
    try:
        milestone.update(data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400
    return "", 204

@api.route("/users/<username>/projects/<project_id>/milestones/<milestone_id>",
           methods=["DELETE"])
@access_validator(owner_auth=True)
def milestone_delete(user, project_id, milestone_id):
    milestone = db.session.query(Milestone).join(Project).join(User).filter(
                    User.id == user.id, Project.id == project_id,
                    Milestone.id == milestone_id).first()
    if not milestone:
        return "", 404
    db.session.delete(milestone)
    db.session.commit()
    return "", 204

@api.route("/users/<username>/projects/<project_id>/milestones/<milestone_id>"
           "/position", methods=["POST"])
@access_validator(owner_auth=True)
def milestone_position(user, project_id, milestone_id):
    data = request.form.to_dict()
    mid_ref = data.get("after", data.get("before", None))
    if not mid_ref:
        return "", 400 # BAD REQUEST

    milestones = db.session.query(Milestone).join(Project).join(User).filter(
                    User.id == user.id, Project.id == project_id,
                    Milestone.id.in_((int(milestone_id), int(mid_ref)))).all()
    if len(milestones) != 2:
        return "Invalid milestones.", 400 # BAD REQUEST

    if milestones[0].id == int(milestone_id):
        m_query = milestones[0]
        m_ref = milestones[1]
    else:
        m_query = milestones[1]
        m_ref = milestones[0]

    if "before" in data: # move m_query before m_ref
        if m_query.position > m_ref.position:
            m_query.position, m_ref.position = m_ref.position, m_query.position
            db.session.commit()
    else: # move m_query after m_ref
        if m_query.position < m_ref.position:
            m_query.position, m_ref.position = m_ref.position, m_query.position
            db.session.commit()

    return "", 200

################################################################################

################################################################################
# MILESTONES - TASKS

@api.route("/users/<username>/projects/<project_id>/milestones/" + \
           "<milestone_id>/tasks", methods=["GET"])
@access_validator(owner_auth=False)
def milestone_tasks(user, project_id, milestone_id):
    milestone = db.session.query(Milestone).join(Project).join(User).filter(
                    User.id == user.id, Project.id == project_id,
                    Milestone.id == milestone_id).first()
    if not milestone:
        return "", 404
    data = [ task.get_info() for task in milestone.tasks ]
    for task in data:
        task["uri"] = url_for("api.milestone_task_get", task_id=task["id"],
                              milestone_id=milestone.id,
                              project_id=project_id, username=user.username) 
    return jsonify(data), 200

@api.route("/users/<username>/projects/<project_id>/milestones/" +
           "<milestone_id>/tasks", methods=["POST"])
@access_validator(owner_auth=True)
def milestone_task_create(user, project_id, milestone_id):
    milestone = db.session.query(Milestone).join(Project).join(User).filter(
                    User.id == user.id, Project.id == project_id,
                    Milestone.id == milestone_id).first()
    if not milestone:
        return "", 404
    
    data = request.form.to_dict()
    if "title" not in data or "deadline" not in data:
        return "", 400

    try:
        task = milestone.add_task(**data)
    except sqlalchemy.orm.StatementError:
        db.session.rollback()
        return "", 400
   
    response = Response("")
    response.status_code = 201
    response.headers["Location"] = url_for("api.milestone_task_get",
                                           username=user.username, 
                                           project_id=project_id,
                                           milestone_id=milestone_id,
                                           task_id=task.id)
    return response

@api.route("/users/<username>/projects/<project_id>/milestones/" + \
           "<milestone_id>/tasks/<task_id>", methods=["GET"])
@access_validator(owner_auth=True)
def milestone_task_get(user, project_id, milestone_id, task_id):
    task = db.session.query(Task).join(Milestone).join(Project).join(User).filter(
                User.id == user.id, Project.id == project_id,
                Milestone.id == milestone_id, Task.id == task_id).first()
    if not task:
        return "", 404
    return jsonify(task.to_dict()), 200

@api.route("/users/<username>/projects/<project_id>/milestones/" + \
           "<milestone_id>/tasks/<task_id>", methods=["PUT"])
@access_validator(owner_auth=True)
def milestone_task_edit(user, project_id, milestone_id, task_id):
    task = db.session.query(Task).join(Milestone).join(Project).join(User).filter(
                User.id == user.id, Project.id == project_id,
                Milestone.id == milestone_id, Task.id == task_id).first()
    if not task:
        return "", 404
    data = request.form.to_dict()
    try:
        task.update(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400
    return "", 204

@api.route("/users/<username>/projects/<project_id>/milestones/" + \
           "<milestone_id>/tasks/<task_id>", methods=["DELETE"])
@access_validator(owner_auth=True)
def milestone_task_delete(user, project_id, milestone_id, task_id):
    task = db.session.query(Task).join(Milestone).join(Project).join(User).filter(
                User.id == user.id, Project.id == project_id,
                Milestone.id == milestone_id, Task.id == task_id).first()
    if not task:
        return "", 404
    
    db.session.delete(task)
    db.session.commit()
    return "", 204

################################################################################

################################################################################
# TAGS

@api.route("/tags", methods=["GET"])
@login_required
def tags():
    tags_db = db.session.query(Tag).all()
    data = [ tag.to_dict() for tag in tags_db ]
    return jsonify(data), 200

@api.route("/tags/<name>", methods=["PUT"])
@login_required
def tag_create(name):
    tag = Tag.find_or_create(name)
    return jsonify({"id": tag.id, "name": tag.name}), 201

@api.route("/tags/<name>", methods=["GET"])
def tag_get(name):
    tag = db.session.query(Tag).filter_by(name=name).one_or_none()
    if tag:
        return "", 204
    else:
        return "", 404

@api.route("/tags/<name>", methods=["DELETE"])
def tag_delete(name):
    tag = db.session.query(Tag).filter_by(name=name).one_or_none()
    if tag:
        db.session.delete(tag)
        db.session.commit()
        return "", 204
    else:
        return "", 404

################################################################################

################################################################################
# EVENTS

@api.route("/users/<username>/events", methods=["GET"])
@access_validator(owner_auth=False)
def events(user):
    data = [ event.get_info() for event in user.events.all() ]
    for event in data:
        event["uri"] = url_for("api.event_get", username=user.username,
                               event_id=event["id"])
    return jsonify(data), 200

@api.route("/users/<username>/events", methods=["POST"])
@access_validator(owner_auth=True)
def event_create(user):
    data = request.form.to_dict()
    if not {"title", "start", "end"} <= set(data.keys()):
        return "", 400

    try:
        event = user.add_event(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400

    response = Response("")
    response.status_code = 201
    response.headers["Location"] = url_for("api.event_get", event_id=event.id,
                                           username=user.username)
    return response

@api.route("/users/<username>/events/<event_id>", methods=["GET"])
@access_validator(owner_auth=False)
def event_get(user, event_id):
    event = db.session.query(Event).join(User).filter(User.id == user.id,
                    Event.id == event_id).one_or_none()
    if not event:
        return "", 404
    return jsonify(event.to_dict()), 200

@api.route("/users/<username>/events/<event_id>", methods=["PUT"])
@access_validator(owner_auth=True)
def event_edit(user, event_id):
    event = db.session.query(Event).join(User).filter(User.id == user.id,
                    Event.id == event_id).one_or_none()
    if not event:
        return "", 404

    data = request.form.to_dict()
    try:
        event.update(**data)
    except sqlalchemy.exc.StatementError:
        db.session.rollback()
        return "", 400

    return "", 204

@api.route("/users/<username>/events/<event_id>", methods=["DELETE"])
@access_validator(owner_auth=True)
def event_delete(user, event_id):
    event = db.session.query(Event).join(User).filter(
                User.id == user.id, Event.id == event_id).one_or_none()
    if not event:
        return "", 404
    db.session.delete(event)
    db.session.commit()
    return "", 204

###############################################################################