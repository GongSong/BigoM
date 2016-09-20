from flask import Blueprint

host = Blueprint('host', __name__)

from . import views
