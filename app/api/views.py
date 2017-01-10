import functools

from flask import jsonify
from flask_login import current_user
import sqlalchemy

from app import login_manager, db
from app.api import api
from app.models import User, Task


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

@api.route("/<username>", methods=["GET"])
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

@api.route("/<username>", methods=["PUT"])
def user_create():
    pass

@api.route("/<username>", methods=["POST"])
def user_edit():
    pass

@api.route("/<username>", methods=["DELETE"])
@access_validator()
def user_delete(user):
    pass

################################################################################

################################################################################
# TASKS

@api.route("/<username>/tasks", methods=["GET"])
@access_validator(owner_auth=False)
def tasks(user):
    return "OK", 200


@api.route("/<username>/tasks", methods=["POST"])
@access_validator()
def task_create(user):
    pass

################################################################################

################################################################################
# TASK

@api.route("/<username>/tasks/<task_id>", methods=["GET"])
@access_validator(owner_auth=False)
def task_get(user, task_id):
    pass

@api.route("/<username>/tasks/<task_id>", methods=["PUT"])
@access_validator()
def task_update(user, task_id):
    pass


################################################################################