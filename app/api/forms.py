from wtforms import TextAreaField, StringField, SelectField, SubmitField, IntegerField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
import datetime

#HealthChecks Request Form
allowed_time_units = [
    ("hours", "Hours"),
    ("days", "Days"),
    ("weeks", "Weeks"),
    ("months", "Months"),
]

class HealthChecksRequestForm(FlaskForm):
    input_number = IntegerField("Number", validators = [DataRequired(), NumberRange(min=1, max=12)])
    time_unit = SelectField("Unit", choices=allowed_time_units, validators=[DataRequired()])




# GRAPHQL FORM
class GraphQLRequestForm(FlaskForm): 
    #Query is a text area, here number of rows defines the length of the element 
    query = TextAreaField("Query", render_kw={"rows": 20, "autofocus": True}, validators=[DataRequired()] ) 
    context_id = StringField("Context ID", validators=[DataRequired()]) 
    workspace_id = StringField("Workspace ID", validators=[DataRequired()]) 
    executing_user_id = StringField("Executing User ID", validators=[DataRequired()]) 
    executing_user_password = StringField("Executing User Password", validators=[DataRequired()])



"""
REST API Form
"""

rest_api_request_types = [
    ("get", "GET"),
    ("post", "POST"),
    ("put", "PUT"),
    ("patch", "PATCH"),
    ("delete", "DELETE")
]

rest_api_endpoint = [
    ("/restapiv2", "/restapiv2"),
    #("/system-management", "/system-management")
]

rest_api_category = [
    ('/assets', 'Assets'), ('/attributes', 'Attributes'), ('/background-processes', 'Background-Processes'), ('/background-process-types', 'Background-Process-Types'), ('/classifications', 'Classifications'), ('/data-container-types', 'Data-Container-Types'), ('/data-type-groups', 'Data-Type-Groups'), ('/entities', 'Entities'), ('/event-processors', 'Event-Processors'), ('/export', 'Export'), ('/import', 'Import'), ('/gateway-integration-endpoints', 'Gateway-Integration-Endpoints'), ('/inbound-integration-endpoints', 'Inbound-Integration-Endpoints'), ('/list-of-values', 'List-Of-Values'), ('/object-types', 'Object-Types'), ('/outbound-integration-endpoints', 'Outbound-Integration-Endpoints'), ('/products', 'Products'), ('/reference-types', 'Reference-Types'), ('/reports', 'Reports'), ('/units', 'Units'), ('/user-groups', 'User-Groups'), ('/users', 'Users'), ('/workflows', 'Workflows'),
    ('/workflow-tasks', 'Workflow-Tasks')
]

rest_api_path = [
    ('/assets', '/assets'), 
    ('/assets/search', '/assets/search'), ('/assets/{id}', '/assets/{id}'), ('/assets/{id}/approval-status', '/assets/{id}/approval-status'), ('/assets/{id}/approve', '/assets/{id}/approve'), ('/assets/{id}/content', '/assets/{id}/content'), ('/assets/{id}/incoming-references/{referenceTypeId}', '/assets/{id}/incoming-references/{referenceTypeId}'), ('/assets/{id}/references/{referenceTypeId}', '/assets/{id}/references/{referenceTypeId}'), ('/assets/{id}/references/{referenceTypeId}/{targetId}', '/assets/{id}/references/{referenceTypeId}/{targetId}'), ('/assets/{id}/references/{referenceTypeId}/{targetId}/values/{attributeId}', '/assets/{id}/references/{referenceTypeId}/{targetId}/values/{attributeId}'), ('/assets/{id}/values/{attributeId}', '/assets/{id}/values/{attributeId}'), ('/assets/{id}/approve-delete', '/assets/{id}/approve-delete'), ('/assets/{id}/purge', '/assets/{id}/purge'), ('/attributes/{id}', '/attributes/{id}'), ('/background-processes/{id}', '/background-processes/{id}'), ('/background-processes/{id}/execution-report', '/background-processes/{id}/execution-report'), ('/background-processes/{id}/attachments', '/background-processes/{id}/attachments'), ('/background-processes/{id}/attachments/{attachmentId}', '/background-processes/{id}/attachments/{attachmentId}'), ('/background-processes/{id}/attachments/{attachmentId}/content', '/background-processes/{id}/attachments/{attachmentId}/content'), ('/background-process-types', '/background-process-types'), ('/background-process-types/{typeId}/processes', '/background-process-types/{typeId}/processes'), ('/classifications', '/classifications'), ('/classifications/search', '/classifications/search'), ('/classifications/{id}', '/classifications/{id}'), ('/classifications/{id}/approval-status', '/classifications/{id}/approval-status'), ('/classifications/{id}/approve', '/classifications/{id}/approve'), ('/classifications/{id}/assets', '/classifications/{id}/assets'), ('/classifications/{id}/children', '/classifications/{id}/children'), ('/classifications/{id}/incoming-references/{referenceTypeId}', '/classifications/{id}/incoming-references/{referenceTypeId}'), ('/classifications/{id}/references/{referenceTypeId}', '/classifications/{id}/references/{referenceTypeId}'), ('/classifications/{id}/references/{referenceTypeId}/{targetId}', '/classifications/{id}/references/{referenceTypeId}/{targetId}'), ('/classifications/{id}/references/{referenceTypeId}/{targetId}/values/{attributeId}', '/classifications/{id}/references/{referenceTypeId}/{targetId}/values/{attributeId}'), ('/classifications/{id}/values/{attributeId}', '/classifications/{id}/values/{attributeId}'), ('/classifications/{id}/approve-delete', '/classifications/{id}/approve-delete'), ('/classifications/{id}/purge', '/classifications/{id}/purge'), ('/data-container-types/{id}', '/data-container-types/{id}'), ('/data-type-groups/{id}', '/data-type-groups/{id}'), ('/entities', '/entities'), ('/entities/find-similar', '/entities/find-similar'), ('/entities/match-and-merge', '/entities/match-and-merge'), ('/entities/search', '/entities/search'), ('/entities/{id}', '/entities/{id}'), ('/entities/{id}/approval-status', '/entities/{id}/approval-status'), ('/entities/{id}/approve', '/entities/{id}/approve'), ('/entities/{id}/children', '/entities/{id}/children'), ('/entities/{id}/data-containers/{dataContainerTypeId}', '/entities/{id}/data-containers/{dataContainerTypeId}'), ('/entities/{id}/incoming-references/{referenceTypeId}', '/entities/{id}/incoming-references/{referenceTypeId}'), ('/entities/{id}/references/{referenceTypeId}', '/entities/{id}/references/{referenceTypeId}'), ('/entities/{id}/references/{referenceTypeId}/{targetId}', '/entities/{id}/references/{referenceTypeId}/{targetId}'), ('/entities/{id}/references/{referenceTypeId}/{targetId}/values/{attributeId}', '/entities/{id}/references/{referenceTypeId}/{targetId}/values/{attributeId}'), ('/entities/{id}/values/{attributeId}', '/entities/{id}/values/{attributeId}'), ('/entities/{id}/approve-delete', '/entities/{id}/approve-delete'), ('/entities/{id}/purge', '/entities/{id}/purge'), ('/event-processors', '/event-processors'), ('/event-processors/{id}', '/event-processors/{id}'), ('/event-processors/{id}/disable', '/event-processors/{id}/disable'), ('/event-processors/{id}/enable', '/event-processors/{id}/enable'), ('/event-processors/{id}/execution-report', '/event-processors/{id}/execution-report'), ('/event-processors/{id}/invoke', '/event-processors/{id}/invoke'), ('/event-processors/{id}/queue/disable', '/event-processors/{id}/queue/disable'), ('/event-processors/{id}/queue/enable', '/event-processors/{id}/queue/enable'), ('/event-processors/{id}/queue/number-of-unread-events', '/event-processors/{id}/queue/number-of-unread-events'), ('/event-processors/{id}/queue/status', '/event-processors/{id}/queue/status'), ('/event-processors/{id}/statistics', '/event-processors/{id}/statistics'), ('/event-processors/{id}/status', '/event-processors/{id}/status'), ('/export/{exportConfigurationId}', '/export/{exportConfigurationId}'), ('/import/{importConfigurationId}', '/import/{importConfigurationId}'), ('/gateway-integration-endpoints', '/gateway-integration-endpoints'), ('/gateway-integration-endpoints/{id}', '/gateway-integration-endpoints/{id}'), ('/gateway-integration-endpoints/{id}/enable', '/gateway-integration-endpoints/{id}/enable'), ('/gateway-integration-endpoints/{id}/disable', '/gateway-integration-endpoints/{id}/disable'), ('/gateway-integration-endpoints/{id}/status', '/gateway-integration-endpoints/{id}/status'), ('/inbound-integration-endpoints', '/inbound-integration-endpoints'), ('/inbound-integration-endpoints/{id}', '/inbound-integration-endpoints/{id}'), ('/inbound-integration-endpoints/{id}/disable', '/inbound-integration-endpoints/{id}/disable'), ('/inbound-integration-endpoints/{id}/enable', '/inbound-integration-endpoints/{id}/enable'), ('/inbound-integration-endpoints/{id}/execution-report', '/inbound-integration-endpoints/{id}/execution-report'), ('/inbound-integration-endpoints/{id}/invoke', '/inbound-integration-endpoints/{id}/invoke'), ('/inbound-integration-endpoints/{id}/statistics', '/inbound-integration-endpoints/{id}/statistics'), ('/inbound-integration-endpoints/{id}/status', '/inbound-integration-endpoints/{id}/status'), ('/inbound-integration-endpoints/{id}/upload', '/inbound-integration-endpoints/{id}/upload'), ('/inbound-integration-endpoints/{id}/upload-and-invoke', '/inbound-integration-endpoints/{id}/upload-and-invoke'), ('/inbound-integration-endpoints/{id}/upload-direct', '/inbound-integration-endpoints/{id}/upload-direct'), ('/inbound-integration-endpoints/{id}/worker-processes', '/inbound-integration-endpoints/{id}/worker-processes'), ('/list-of-values/{id}', '/list-of-values/{id}'), ('/list-of-values/{id}/value-entries', '/list-of-values/{id}/value-entries'), ('/object-types/{id}', '/object-types/{id}'), ('/outbound-integration-endpoints', '/outbound-integration-endpoints'), ('/outbound-integration-endpoints/{id}', '/outbound-integration-endpoints/{id}'), ('/outbound-integration-endpoints/{id}/disable', '/outbound-integration-endpoints/{id}/disable'), ('/outbound-integration-endpoints/{id}/enable', '/outbound-integration-endpoints/{id}/enable'), ('/outbound-integration-endpoints/{id}/execution-report', '/outbound-integration-endpoints/{id}/execution-report'), ('/outbound-integration-endpoints/{id}/invoke', '/outbound-integration-endpoints/{id}/invoke'), ('/outbound-integration-endpoints/{id}/queue/disable', '/outbound-integration-endpoints/{id}/queue/disable'), ('/outbound-integration-endpoints/{id}/queue/enable', '/outbound-integration-endpoints/{id}/queue/enable'), ('/outbound-integration-endpoints/{id}/queue/number-of-unread-events', '/outbound-integration-endpoints/{id}/queue/number-of-unread-events'), ('/outbound-integration-endpoints/{id}/queue/status', '/outbound-integration-endpoints/{id}/queue/status'), ('/outbound-integration-endpoints/{id}/statistics', '/outbound-integration-endpoints/{id}/statistics'), ('/outbound-integration-endpoints/{id}/status', '/outbound-integration-endpoints/{id}/status'), ('/outbound-integration-endpoints/{id}/worker-processes', '/outbound-integration-endpoints/{id}/worker-processes'), ('/products', '/products'), ('/products/search', '/products/search'), ('/products/{id}', '/products/{id}'), ('/products/{id}/approval-status', '/products/{id}/approval-status'), ('/products/{id}/approve', '/products/{id}/approve'), ('/products/{id}/children', '/products/{id}/children'), ('/products/{id}/data-containers/{dataContainerTypeId}', '/products/{id}/data-containers/{dataContainerTypeId}'), ('/products/{id}/incoming-references/{referenceTypeId}', '/products/{id}/incoming-references/{referenceTypeId}'), ('/products/{id}/references/{referenceTypeId}', '/products/{id}/references/{referenceTypeId}'), ('/products/{id}/references/{referenceTypeId}/{targetId}', '/products/{id}/references/{referenceTypeId}/{targetId}'), ('/products/{id}/references/{referenceTypeId}/{targetId}/values/{attributeId}', '/products/{id}/references/{referenceTypeId}/{targetId}/values/{attributeId}'), ('/products/{id}/values/{attributeId}', '/products/{id}/values/{attributeId}'), ('/products/{id}/approve-delete', '/products/{id}/approve-delete'), ('/products/{id}/purge', '/products/{id}/purge'), ('/reference-types/{id}', '/reference-types/{id}'), ('/reports/historic-changes/{reportID}', '/reports/historic-changes/{reportID}'), ('/reports/historic-changes/{reportID}/clean-up', '/reports/historic-changes/{reportID}/clean-up'), ('/units/{id}', '/units/{id}'), ('/user-groups/{id}', '/user-groups/{id}'), ('/user-groups/{id}/users', '/user-groups/{id}/users'), ('/user-groups/{id}/children', '/user-groups/{id}/children'), ('/users/{id}', '/users/{id}'), ('/users/{id}/randomize-step-password', '/users/{id}/randomize-step-password'), ('/users/{id}/add-to-group', '/users/{id}/add-to-group'), ('/users/{id}/remove-from-group', '/users/{id}/remove-from-group'), ('/workflows', '/workflows'), ('/workflows/{id}', '/workflows/{id}'), ('/workflows/{id}/instances', '/workflows/{id}/instances'), ('/workflows/{id}/instances/{instanceId}', '/workflows/{id}/instances/{instanceId}'), ('/workflow-tasks/search', '/workflow-tasks/search'), ('/workflow-tasks/{id}', '/workflow-tasks/{id}'), ('/workflow-tasks/{id}/claim', '/workflow-tasks/{id}/claim'), ('/workflow-tasks/{id}/events', '/workflow-tasks/{id}/events'), ('/workflow-tasks/{id}/trigger-event', '/workflow-tasks/{id}/trigger-event'), ('/workflow-tasks/{id}/release', 
    '/workflow-tasks/{id}/release')
]

#The Rest API form. It has no submit field, as submission is done via button in the form which has the function type value set. 
class RestAPIRequestForm(FlaskForm): 
    #Default fields shown at the top (may be autofilled is user added them while adding a system) 
    context_id = StringField("Context ID", validators=[DataRequired()]) 
    workspace_id = StringField("Workspace ID", validators=[DataRequired()]) 
    executing_user_id = StringField("Executing User ID", validators=[DataRequired()]) 
    executing_user_password = StringField("Executing User Password", validators=[DataRequired()])
    
    #Dropdown Fields for REST API
    request_type         = SelectField("Type", choices=rest_api_request_types, validators=[DataRequired()])
    request_endpoint     = SelectField("Endpoint", choices=rest_api_endpoint, validators=[DataRequired()])
    request_category     = SelectField("Category", choices=rest_api_category, validators=[DataRequired()])
    request_path         = SelectField("Path", choices=rest_api_path, validators=[DataRequired()])
    request_body         = TextAreaField("Request Body", render_kw={"rows": 20})

    def validate_request_body(self, field):
        if self.request_type.data in ['post', 'put', 'patch'] and not field.data:
            raise ValidationError("Request Body is required for POST, PUT and PATCH requests.")


"""
Console Form
"""
integration_endpoint_types = [
    ("oiep", "Outbound Integration Endpoints"),
    ("iiep", "Inbound Integration Endpoints"),
    ("giep", "Gateway Integration Endpoints"),
    ("ep", "Event Processors")
]

integration_endpoint_actions = [
    ("list", "Fetch basic details"),
    ("list_detailed", "Fetch advanced details"),
    ("invoke", "Invoke"),
    ("enable", "Enable"),
    ("disable", "Disable"),

]

integration_endpoint_choices = [
    ("all", "All"),
    ("specified", "Specified ID's only.")
]

#The Rest API form. It has no submit field, as submission is done via button in the form which has the function type value set. 
class ConsoleRequestForm(FlaskForm): 
    #Default fields shown at the top (may be autofilled is user added them while adding a system) 
    context_id = StringField("Context ID") 
    workspace_id = StringField("Workspace ID") 
    executing_user_id = StringField("Executing User ID", validators=[DataRequired()]) 
    executing_user_password = StringField("Executing User Password", validators=[DataRequired()])
    
    #Integration Endpoint Dropdown Fields
    integration_endpoint_type = SelectField("Select Type", choices=integration_endpoint_types)
    integration_endpoint_action = SelectField("Select Action", choices=integration_endpoint_actions)
    integration_endpoint_choice = SelectField("Choose Target", choices=integration_endpoint_choices)

    #Specified Integration Endpoint ID Field
    integration_endpoint_ids = StringField("Target Object STEP IDs", validators=[Length(max=10000, message="Input too large.")])