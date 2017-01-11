import functools
from datetime import datetime

from flask import jsonify, request, Response, url_for
from flask_login import current_user
import sqlalchemy

from app import login_manager, db
from app.api import api
from app.models import User, Task


# Read This
# http://michal.karzynski.pl/blog/2016/06/19/building-beautiful-restful-apis-using-flask-swagger-ui-flask-restplus/


# Create decorator for access restriction
def access_validator(owner_auth=True, response=""):
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
                return response, 404
            if not owner_auth and not user.public and current_user.username != username:
                return response, 404 
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
        task["uri"] = "/" + user.username + "/tasks/" + str(task["id"])
    for project in rrepr["projects"]:
        project["uri"] = "/" + user.username + "/projects/" + str(project["id"])
    for note in rrepr["notes"]:
        note["uri"] = "/" + user.username + "/notes/" + str(note["id"])
    return jsonify(rrepr), 200

@api.route("/users/<username>", methods=["PUT"])
@access_validator()
def user_edit(user):
    mod_flag = False
    if "public" in request.form:
        if request.form["public"].upper() in ("T", "TRUE", "YES", "Y"):
            user.public = True
            mod_flag = True
    if "new_password" in request.form and "new_password2" in request.form:
        if request.form["new_password"] == request.form["new_password2"]:
            user.password = request.form["new_password"]
            mod_flag = True
    if mod_flag:
        db.session.commit()
    return "", 200

@api.route("/users", methods=["POST"])
def user_create():
    if not "username" in request.form:
        return "No username.", 400
    if not "password" in request.form or not "password2" in request.form:
        return "No passward or password confirmation.", 400
    if request.form["password"] != request.form["password2"]:
        return "Invalid password confirmation.", 400

    user = User(username=request.form["username"], 
                password=request.form["password"])
    db.session.add(user)
    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        return "Username already exists.", 409
    return "", 201

@api.route("/users/<username>", methods=["DELETE"])
@access_validator()
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
        task["uri"] = "/api/users/" + user.username + "/tasks/" + \
                      str(task["id"])
    return jsonify(data), 200

@api.route("/users/<username>/tasks", methods=["POST"])
@access_validator()
def task_create(user):
    data = request.form.to_dict()
    # Two fields are required
    if not "title" in data or not "deadline" in data:
        return "", 400
    data["deadline"] = datetime.strptime(data["deadline"], "%Y-%m-%d %H:%M")
    # Ignore redundat data from request
    data = { key: value for key, value in data.items() 
                        if key in Task.__table__.columns.keys() }
    task = user.add_task(**data)

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
        return "", 404
    return jsonify(task.to_dict()), 200

@api.route("/users/<username>/tasks/<task_id>", methods=["PUT"])
@access_validator()
def task_edit(user, task_id):
    task = db.session.query(Task).join(User).filter(
            User.id == user.id, Task.id == task_id).first()
    if not task:
        return "", 404

    data = request.form.to_dict()
    if "deadline" in data:
        data["deadline"] = datetime.strptime(data["deadline"], "%Y-%m-%d %H:%M")
    data = { key: value for key, value in data.items() 
                        if key in Task.__table__.columns.keys() }
    task.update(**data)
    return "", 200

################################################################################

################################################################################
# PROJECTS


################################################################################

################################################################################
# MILESTONES


################################################################################

################################################################################
# NOTES

################################################################################
