from flask import Blueprint

eboard = Blueprint("eboard", __name__)

from . import views