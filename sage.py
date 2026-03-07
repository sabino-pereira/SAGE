#Imports for use in shell context function
import sqlalchemy as sa
import sqlalchemy.orm as orm
from app.models import User, System, Link, PageVisit
from app import create_app, db

#Create the app using application factory
flaskApp = create_app()


#This decorator comes into play when 'flask shell' is run from the terminal. It's used to automate the import of the specified modules for testing
@flaskApp.shell_context_processor
def make_shell_context():
    """
    This function is to help in testing and debugging. 
    It is activated when the 'flask shell' command is run in the venv.
    It's purpose is to initiate and import the dependencies needed for testing features like DB changes.
    """
    return {'sa': sa, 'so': orm, 'db': db, 'User': User, 'System': System, 'Link': Link, 'Visit': PageVisit}