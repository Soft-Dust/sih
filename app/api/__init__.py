# This file makes the api directory a Python package
from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import routes