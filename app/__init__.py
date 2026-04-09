from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_session import Session
from flask_moment import Moment
from config import Config
import random
from datetime import datetime, timezone, timedelta

#Initiate DB object
db = SQLAlchemy()

#Initiate DB Migrate object
migrate = Migrate()

#Initiate login helper object and set login route/function name
login = LoginManager()
login.login_view = "auth.login"

#Initiate Flask Moment Object
moment = Moment()

#Inititate Flask Session object
flask_session = Session()

# Dictionary for module usage
# Defined globally to avoid recreation on every request
TRACK_PAGES_DICTIONARY = {
    "core.home": "Home",
    "core.systems": "Systems",
    "core.tools": "Tools",
    "core.knowledge_hub": "Knowledge Hub",
    "core.admin": "Admin",
    "auth.logout": "Logout",
    "errors.not_found_error": "404 Error Page",
    "errors.content_too_large": "413 Error Page",
    "errors.app_errorhandler": "500 Error Page",
    "api.graphql": "GraphQL",
    "api.rest_api": "Rest API",
    "api.console": "Console",
    "api.healthcheck": "Healthcheck",
    "api.sensors": "Sensors",
    "api.sensor_details": "Sensor Details",
}

#Application Factory Function
def create_app(config_class=Config):
    #Create the application instance and pass config
    flaskApp = Flask(__name__)
    flaskApp.config.from_object(Config)

    #Register application instance with extensions
    db.init_app(flaskApp)
    migrate.init_app(flaskApp, db)
    login.init_app(flaskApp)
    moment.init_app(flaskApp)
    flask_session.init_app(flaskApp)

    """
    Blueprint Registration
    """
    #Import and register the core blueprint -> Used for all application core functions
    from app.core import bp as core_bp
    flaskApp.register_blueprint(core_bp)
    
    #Import and register the login blueprint -> Used for user login, register,etc. functions
    from app.auth import bp as auth_bp
    flaskApp.register_blueprint(auth_bp, url_prefix="/auth")

    #Import and register the errors blueprint -> Used for error routing functions
    from app.errors import bp as errors_bp
    flaskApp.register_blueprint(errors_bp, url_prefix="/error")

    #Import and register the api blueprint -> Used for all api functions
    from app.api import bp as api_bp
    flaskApp.register_blueprint(api_bp, url_prefix="/api")

    # Import and register documentation module -> Used for documentation
    from app.docs import bp as docs_bp
    flaskApp.register_blueprint(docs_bp, url_prefix="/docs")

  
    #Import data from the 'app' module. This import is defined at the bottom to avoid circular imports
    from app.models import PageVisit

    """
    Global Variables
    """
    #Set variables in g object before each request. This keeps them updated and accessible throught the app
    @flaskApp.before_request
    def load_global_settings():
        # Find currently selected system by the user
        from app.core.core_utils import get_selected_system_from_db
        g.selected_system = get_selected_system_from_db()
        
        # Set application config variables from the config
        g.registration_allowed = flaskApp.config["REGISTRATION_ALLOWED"]
        g.max_systems = flaskApp.config["MAX_SYSTEMS"]
        g.max_quick_access_links = flaskApp.config["MAX_QUICK_ACCESS_LINKS"]
        g.api_timeout = flaskApp.config["API_REQUEST_TIMEOUT"]
        g.api_bearer_token_ttl = flaskApp.config["API_BEARER_TOKEN_TTL"]
        
        # Set variables for text data
        g.graphql_sample_query = flaskApp.config["GRAPQL_SAMPLE_QUERY"]
        g.selected_quote = random.choice(flaskApp.config["QUOTES_LIST"]) or "That wasn't supposed to happen!"


    """
    Track User Activity
    """
    # Track user page visits
    @flaskApp.before_request
    def track_user_activity():
        if not current_user.is_anonymous:
            #Track User Last Active Time
            current_user.update_last_active()

            #Track user visited pages for users who are requesting a page and not an asset, and it's not a POST request (form submission)
            if request.endpoint and request.endpoint in TRACK_PAGES_DICTIONARY and request.method == 'GET':
                visited_page_formatted_name = TRACK_PAGES_DICTIONARY[request.endpoint]
                PageVisit.record_visit(current_user.id, visited_page_formatted_name)

    
    """
    Pass common variables to all templates
    """
    # Make g variables accessible by name in templates without having to pass the g object
    @flaskApp.context_processor
    def inject_global_settings_for_templates():
        return dict(
            selected_system = g.get('selected_system'),
            selected_quote = g.get('selected_quote'),
            project_link = flaskApp.config["PROJECT_LINK"],
            app_name = flaskApp.config["APP_NAME"],
            app_name_full = flaskApp.config["APP_NAME_FULL"],
            registration_allowed = flaskApp.config["REGISTRATION_ALLOWED"],
            app_version = flaskApp.config["APP_VERSION"]
        )

    
    return flaskApp








    