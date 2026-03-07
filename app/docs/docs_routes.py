from app.docs import bp
from flask import render_template



# Documentation Home
@bp.route("/")
def docs_homepage():
    return render_template("docs.html", title="Documentation")

# Getting Started
@bp.route("/getting-started")
def getting_started():
    return render_template("getting_started_docs.html", title="Getting Started")

# Systems Documentation
@bp.route("/core-docs")
def core():
    return render_template("core_docs.html", title="Core Documentation")

# API Documentation
@bp.route("/api")
def api():
    return render_template("api_docs.html", title="API Documentation")


# Healthchecks Documentation
@bp.route("/monitoring")
def monitoring():
    return render_template("monitoring_docs.html", title="Monitoring Documentation")


# Systems Documentation
@bp.route("/tools")
def tools():
    return render_template("tools_docs.html", title="Tools Documentation")














