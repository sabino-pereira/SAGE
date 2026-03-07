from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, ValidationError, url, Length
from app import db
from app.models import System, System_Type, Deployment_Type
from flask_login import current_user
import sqlalchemy as sa
from urllib.parse import urlparse


#The form used to add a new system by a user
class AddSystemForm(FlaskForm):
    #Mandatory system details
    system_name = StringField("System Name", validators= [DataRequired(), Length(min=2, max=15, message="System Name should be between %(min)d and %(max)d characters long.")])
    system_url = StringField("System URL", validators=[DataRequired(), url()])
    system_type = SelectField("System Type", choices=[(s.name, s.value) for s in System_Type], validators=[DataRequired()])
    deployment_type = SelectField("Deployment Type", choices=[(s.name, s.value) for s in Deployment_Type], validators=[DataRequired()])
    
    #Optional system details (can also be provided at runtime)
    step_user_id = StringField("User ID", validators=[DataRequired(), Length(max=40)])
    step_user_password = StringField("User Password", validators=[DataRequired(), Length(max=100)])
    default_context = StringField("Default Context", validators=[DataRequired(), Length(max=40)])
    default_workspace = StringField("Default Workspace", validators=[DataRequired(), Length(max=40)])
    
    #Submit button
    submit = SubmitField("Add System")

    #Check if system with same url is not already added (to prevent redundancy)
    def validate_system_url(self, system_url):
        parsed_url = "https://" + urlparse(system_url.data).netloc
        system = db.session.scalar(
            sa.select(System).where(System.system_url == parsed_url, System.user_id == current_user.id)
        )
        if system is not None:
            raise ValidationError("You have already added this system!")

    #Check if system with same name is not already added (to prevent confusion)  
    def validate_system_name(self, system_name):
        system = db.session.scalar(
            sa.select(System).where(System.system_name == system_name.data, System.user_id == current_user.id)
        )
        if system is not None:
            raise ValidationError("You already have another system added with the same name!")


#The form used to add a new system by a user
class EditSystemForm(FlaskForm):
    #Mandatory system details
    edit_system_id = IntegerField("System ID", validators= [DataRequired()])
    edit_system_name = StringField("System Name", validators= [DataRequired(), Length(min=2, max=15, message="System Name should be between %(min)d and %(max)d characters long.")])
    edit_system_url = StringField("System URL", validators=[DataRequired(), url()])
    edit_system_type = SelectField("System Type", choices=[(s.name, s.value) for s in System_Type], validators=[DataRequired()])
    edit_deployment_type = SelectField("Deployment Type", choices=[(s.name, s.value) for s in Deployment_Type], validators=[DataRequired()])
    
    #Optional system details
    edit_step_user_id = StringField("User ID", validators=[DataRequired(), Length(max=40)])
    edit_step_user_password = StringField("User Password", validators=[DataRequired(), Length(max=100)])
    edit_default_context = StringField("Default Context", validators=[DataRequired(), Length(max=40)])
    edit_default_workspace = StringField("Default Workspace", validators=[DataRequired(), Length(max=40)])
    
    #Submit button
    edit_submit = SubmitField("Confirm System Edits")

    def __init__(self, *args, **kwargs):
        self.edit_system_id = kwargs.pop('edit_system_id', None) 
        super(EditSystemForm, self).__init__(*args, **kwargs)

    #Check if system with same url is not already added (to prevent redundancy), except offcourse the system to be edited itself
    def validate_edit_system_url(self, edit_system_url):
        parsed_url = "https://" + urlparse(edit_system_url.data).netloc
        system = db.session.scalar(
            sa.select(System).where(System.system_url == parsed_url, System.user_id == current_user.id, System.id != self.edit_system_id.data)
        )
        if system is not None:
            raise ValidationError("You have already added this system under another name!")

    #Check if system with same name is not already added (to prevent confusion)  
    def validate_edit_system_name(self, edit_system_name):
        system = db.session.scalar(
            sa.select(System).where(System.system_name == edit_system_name.data, System.user_id == current_user.id, System.id != self.edit_system_id.data)
        )
        if system is not None:
            raise ValidationError("You already have another system added with the same name!")   



#The form used to add a new system by a user
class AddLinkForm(FlaskForm):
    #Mandatory system details
    link_name = StringField("Link Name", validators= [DataRequired(), Length(min=2, max=30, message="Link Name should be between %(min)d and %(max)d characters long.")])
    link_url = StringField("Link URL", validators=[DataRequired(), url()])
    
    #Submit button
    submit = SubmitField("Add Link")

# Generic Delete Form
class DeleteForm(FlaskForm):
    submit = SubmitField("Delete")


#The Developer tools form, for various developer utilites. Note that the form is not being submitted to the server, instead it works on the client side.
developer_tools_choices = []
developer_tools_choices.append(("js_beautify", "1. Beautify Javascript Code"))
developer_tools_choices.append(("xml_beautify", "2. Beautify XML Code"))
developer_tools_choices.append(("c2j", "3. CSV list of IP's to STEP JSON format"))
developer_tools_choices.append(("j2c", "4. JSON list of IP's exported from STEP to CSV"))

class DeveloperToolsForm(FlaskForm):
    input_text = TextAreaField("Enter your input...", render_kw={"rows": 20, "autofocus": True}, validators=[DataRequired(), Length(max=10000000, message="Input too large.")])
    action_type = SelectField("Select Action", choices=developer_tools_choices, validators=[DataRequired()])
    submit = SubmitField("Execute")