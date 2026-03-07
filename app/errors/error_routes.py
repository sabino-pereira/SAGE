from flask import render_template, current_app
from app.errors import bp
from app import db

#Route to page for error 404
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template("404.html", title="Page Not Found"), 404


#Route to page for error 413
@bp.app_errorhandler(413)
def content_too_large(error):
    return render_template("413.html", title="Content too Large"), 413

#Route to page for error 500
@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    current_app.logger.error(f"Server Error: {error}")
    return render_template("500.html", title="System Error"), 500