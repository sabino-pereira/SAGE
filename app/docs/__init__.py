from flask import Blueprint

bp = Blueprint("docs", __name__, template_folder="templates")

from app.docs import docs_routes