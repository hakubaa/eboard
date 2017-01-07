from app.api import api

@api.route("/tasks", methods=["GET"])
def get_tasks():
    pass