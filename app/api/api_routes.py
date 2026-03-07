from flask import render_template, flash, redirect, url_for, g, request, session, abort
from flask_login import login_required
from app import db
from app.api import bp
from app.core.core_utils import clear_session_variables
import requests
from app.api.api_utils import console_execute, parseXMLResponse, parse_details_xml, api_execute, parse_healthcheck_response
from app.api.forms import GraphQLRequestForm, RestAPIRequestForm, ConsoleRequestForm, HealthChecksRequestForm
from graphql import parse, print_ast
from wtforms import StringField
from wtforms.validators import DataRequired
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone

"""
Healthchecks Routes
"""
#The sensors page, only a shell page, with a subtemplate that will render when sensors response is received from STEP
@bp.route("/sensors")
@login_required
def sensors():
    if g.selected_system:
        return render_template("sensors.html", title="Monitoring Sensors")
    else:
        flash("First Add or Select a STEP system!", "warning")
        return redirect(url_for("core.systems"))


#The ajax route to return sensor details
@bp.route("/sensor_data")
@login_required
def sensor_data():
    if g.selected_system:
        #Default Return (Error Message)
        return_dictionary = {
            "return_code" : "Error",
            "return_html_data" : """
                <div class="text-danger mb-2">
                    <strong>Error:</strong> Could not load sensor data.
                </div>

                <div class="text-muted mb-4">
                    Details: {{error}}
                </div>

                <div class="d-grid gap-2 col-4 mx-auto">
                    <a class="btn btn-primary" href="{{url_for('api.sensors')}}" role="button">Retry</a>
                </div>
            """
        }

        #Replacing Default HTMl with Error Code using parsed_html
        parsed_html = ""

        try:
            #URL for data in xml format
            monitor_url = g.selected_system.system_url + "/admin/monitoring/TrafficLight-local/xml"
            
            #Get Data
            response = requests.get(monitor_url)
            
            #Raise response bad exception
            response.raise_for_status()
            
            #If no exceptions, parse the response data and return a dictionary of output
            sensors = parseXMLResponse(response.text)

            if sensors[0]["name"] == "Parse Error":
                parsed_html = sensors[0]["status"]
            
            else:
                return_dictionary["return_code"] = "Success"
                
                #For Large Screens
                parsed_html = """
                    <div class="table-responsive d-none d-md-block">    
                        <table class="table table-sm" id="custom-sensors-table">
                            <thead>
                                <tr>
                                    <th>Sensor Name</th>
                                    <th>Status</th>
                                    <th class="text-center">More Details</th>
                                </tr>
                            </thead>
                            <tbody id="sensors_table_body">
                """
                
                for sensor in sensors:
                    row_display_class = "table-secondary"
                    if sensor["status"] == "OK":
                        row_display_class = "table-success"
                    elif sensor["status"] == "WARNING":
                        row_display_class = "table-warning"
                    elif sensor["status"] == "CRITICAL":
                        row_display_class = "table-danger"

                    parsed_html += '<tr scope="row" class="{}"> <td>{}</td> <td>{}</td>\
                                        <td class="text-center"><a class="btn btn-primary btn-sm" target="_blank" href="{}">i</a></td>\
                                    </tr>'.format(row_display_class, sensor["name"], sensor["status"], url_for("api.sensor_details", sensorName=sensor["name"]))
                
                parsed_html += """
                            </tbody>
                        </table>
                    </div>
                """

                #For Smaller Screens
                for sensor in sensors:
                    card_display_class = "secondary"
                    if sensor["status"] == "OK":
                        card_display_class = "success"
                    elif sensor["status"] == "WARNING":
                        card_display_class = "warning"
                    elif sensor["status"] == "CRITICAL":
                        card_display_class = "danger"

                    parsed_html += """
                        <div class="d-block d-md-none mb-3" id="sensors_cards">
                            <div class="card border-{}">
                                <div class="card-header text-center text-bg-{}">
                                    {}
                                </div>
                                <div class="card-body">
                                    <div class ="text-center">
                                        <p>Status - {}</p>
                                        <a href="{}" target="_blank">Details</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    """.format(card_display_class, card_display_class, sensor["name"], sensor["status"], url_for("api.sensor_details", sensorName=sensor["name"]))
                

        #Data Fetching Errors
        except requests.exceptions.RequestException as er:
            parsed_html = str(er)

        #Unknown Errors
        except Exception as e:
            parsed_html = str(e)

        if return_dictionary["return_code"] == "Success":
            return_dictionary["return_html_data"] = parsed_html
        else:
            return_dictionary["return_html_data"] = return_dictionary["return_html_data"].replace("{{error}}", parsed_html)
        
        return return_dictionary
    else:
        flash("First Add or Select a STEP system!", "warning")
        return redirect(url_for("core.systems"))

  
#The sensor-details page, will display additional details about an input sensor
@bp.route("/sensor-details/<sensorName>")
@login_required
def sensor_details(sensorName):
    if g.selected_system:   
        try:
            details_url = g.selected_system.system_url + "/admin/monitoring/" + sensorName + "/xml"
            timeout = g.api_timeout or 60
            response = requests.get(details_url, timeout=timeout)
            response.raise_for_status()
            sensor_details_data = parse_details_xml(response.text)

            root = ET.fromstring(response.text)
            ET.indent(root, space="  ")
            raw_data = ET.tostring(root, encoding='unicode')
            return render_template("sensor_details.html", processed_data=sensor_details_data, raw_data=raw_data, errorOccured=False, title="Sensor Details")
        
        except Exception as e:
            return render_template("sensor_details.html", error=str(e), errorOccured=True, title="Sensor Details")
    else:
        flash("First Add or Select a STEP system!", "warning")
        return redirect(url_for("core.systems"))



#The healthcheck page
@bp.route("/healthcheck", methods=["GET", "POST"])
@login_required
def healthcheck():
    if g.selected_system:
        form = HealthChecksRequestForm()
        parsed_response = None
        days_input = None
        
        if form.validate_on_submit():
            healthcheck_query = """
            query queryHealthChecks {
                healthChecks: perfrep_queryHealthChecks {
                    ID
                    name
                    category
                    issueCount
                    severity
                    completedAt
                    status
                    __typename
                }
            }
            """

            # Form Input Time Delta
            input_number = form.input_number.data
            time_unit = form.time_unit.data
            session["healthcheck_input_number"] = input_number
            session["healthcheck_time_unit"] = time_unit

            if time_unit == "hours":
                seconds_count = 3600
            elif time_unit == "weeks":
                seconds_count = 604800
            elif time_unit == "months":
                seconds_count = 2592000
            else:
                seconds_count = 86400
            total_seconds = seconds_count * input_number

            # Current utc timestamp
            current_timestamp = int(datetime.now(timezone.utc).timestamp())

            # Difference between the two calculations
            filter_timestamp = current_timestamp - total_seconds
            
            healthcheck_response_dictionary = api_execute("graphql", healthcheck_query, g.selected_system.step_user_id, g.selected_system.step_user_password)

            if healthcheck_response_dictionary["error"]:
                healthcheck_dictionary_list = "<span class='text-danger text-center'> {} </span>".format(healthcheck_response_dictionary["data"])
            else:
                healthcheck_dictionary_list = parse_healthcheck_response(healthcheck_response_dictionary["data"], filter_timestamp)
            
            session["healthcheck_return_value"] = healthcheck_dictionary_list
                
            #PRG pattern to avoid refresh page errors
            return redirect(url_for("api.healthcheck"))

        healthcheck_dictionary_list = session.get("healthcheck_return_value", default=None)
        form.input_number.data = session.get("healthcheck_input_number", default=7)
        form.time_unit.data = session.get("healthcheck_time_unit", default=None)
        
        if form.input_number.data and form.time_unit.data:
            days_input = str(form.input_number.data) + " " + form.time_unit.data

        return render_template("healthcheck.html", title="Healthchecks", form=form, healthcheck_dictionary_list=healthcheck_dictionary_list, days_input=days_input)
    
    else:
        flash("First Add or Select a STEP system!", "warning")
        return redirect(url_for("core.systems"))




"""
API Routes
"""
@bp.route("/clear-token")
@login_required
def clear_token():
    previous_url = request.referrer
    try:
        #Only available if a system is selected
        if g.selected_system:
            if g.selected_system.bearer_token:
                g.selected_system.bearer_token = None
                db.session.add(g.selected_system)
                db.session.commit()
                flash("Saved bearer token cleared.", "success")
            else:
                flash("No token present to clear", "warning")
        else:
            flash("First Add or Select a STEP system!", "warning")
            return redirect(url_for("core.systems"))
    except Exception:
        db.session.rollback()
        flash("Something went wrong when trying to clear the token", "danger")

    return redirect(previous_url or url_for('core.home'))


#Route for 'Clear' button all API that resets session variables
@bp.route("/clear-api")
@login_required
def clear_api():
    clear_session_variables()
    previous_url = request.referrer
    return redirect(previous_url or url_for('core.home'))



"""
GraphQL Routes
"""
#The GraphQL Page
@bp.route("/graphql", methods=["GET", "POST"])
@login_required
def graphql():
    #Only available if a system is selected
    if g.selected_system:
        try:
            # Get the GraphQL Form
            form = GraphQLRequestForm()

            if form.validate_on_submit():
                #Get the query
                query = str(form.query.data)

                #Save Query in session
                session['graphql_old_query'] = query
                
                # Dynamic Context and Workspace via input if specified
                if "<dynamic-context>" in query:
                    query = query.replace("<dynamic-context>", str(form.context_id.data))
                if "<dynamic-workspace>" in query:
                    query = query.replace("<dynamic-workspace>", str(form.workspace_id.data))                

                #Store Inputs in session
                session["userid"]    = form.executing_user_id.data
                session["password"]  = form.executing_user_password.data
                session["context"]   = form.context_id.data
                session["workspace"] = form.workspace_id.data

                session["graphql_return_value"] = api_execute("graphql", query, form.executing_user_id.data, form.executing_user_password.data)
                
                #PRG pattern to avoid refresh page errors
                return redirect(url_for("api.graphql"))

            #Get input query and result from session
            return_dictionary      = session.get("graphql_return_value", default=None)
            old_query_from_session = session.get("graphql_old_query", default = g.graphql_sample_query)
            
            #Format/Prettify the query
            try:
                document = parse(old_query_from_session)
                form.query.data = print_ast(document)
            except:
                form.query.data = old_query_from_session
            
            #Set Default inputs for the form
            form.executing_user_id.data       = session.get("userid",    default = g.selected_system.step_user_id)
            form.executing_user_password.data = session.get("password",  default = g.selected_system.step_user_password)
            form.context_id.data              = session.get("context",   default = g.selected_system.default_context)
            form.workspace_id.data            = session.get("workspace", default = g.selected_system.default_workspace)

            return render_template("graphql.html", form=form, return_dictionary=return_dictionary, title="GraphQL")
        
        except Exception as e:
            # Rollback any staged db changes and throw a 500 error
            db.session.rollback()
            abort(500)
    
    else:
        flash("First Add or Select a STEP system!", "warning")
        return redirect(url_for("core.systems"))



#Route for 'Prettify' button in GRAPHQL
@bp.route("/prettify-graphql", methods=["POST"])
@login_required
def prettify_graphql():
    input_query = request.get_data(as_text=True)
    query_return_dictionary = {
        "status" : "error",
        "message" : ""
    }
    if not input_query:
        query_return_dictionary["message"] = "Query Empty"
    else:
        try:
            prettified_query = print_ast(parse(input_query))
            query_return_dictionary["status"] = "success"
            query_return_dictionary["message"] = prettified_query
        except Exception as e:
            query_return_dictionary["status"] = "error"
            query_return_dictionary["message"] = str(e)

    return query_return_dictionary



#The Console page
@bp.route("/console", methods=["GET", "POST"])
@login_required
def console():
    #Only available if a system is selected
    if g.selected_system:
        try:
            form = ConsoleRequestForm()
            
            #Console action submission after clicking any button
            if form.validate_on_submit():
                #Console request type is stored as 'button action' in the form
                selected_action = request.form.get("action")

                #Store Inputs in session to have them persist any changes made by the user
                session["userid"]    = form.executing_user_id.data
                session["password"]  = form.executing_user_password.data
                session["context"]   = form.context_id.data
                session["workspace"] = form.workspace_id.data

                session["integration_endpoint_type"]      = form.integration_endpoint_type.data
                session["integration_endpoint_action"]    = form.integration_endpoint_action.data
                session["integration_endpoint_choice"]    = form.integration_endpoint_choice.data
                session["integration_endpoint_ids"]       = form.integration_endpoint_ids.data

                #Store output in session as we want it available after page redirect
                session["console_return_value"] = console_execute(
                    selected_action, 
                    user_id                     = form.executing_user_id.data, 
                    user_password               = form.executing_user_password.data, 
                    context                     = form.context_id.data, 
                    workspace                   = form.workspace_id.data,
                    integration_endpoint_type   = form.integration_endpoint_type.data,
                    integration_endpoint_action = form.integration_endpoint_action.data,
                    integration_endpoint_choice = form.integration_endpoint_choice.data,
                    integration_endpoint_ids    = form.integration_endpoint_ids.data
                )
                
                #This redirect is to avoid form-resubmission popup/error when page is refreshed
                return redirect(url_for("api.console"))


            #Set Default inputs for the form, normally it's the data set by the user when adding a system, changed by user has overridden any of it
            form.executing_user_id.data               = session.get("userid", default = g.selected_system.step_user_id)
            form.executing_user_password.data         = session.get("password", default = g.selected_system.step_user_password)
            form.context_id.data                      = session.get("context", default = g.selected_system.default_context)
            form.workspace_id.data                    = session.get("workspace", default = g.selected_system.default_workspace)
            form.integration_endpoint_type.data       = session.get("integration_endpoint_type", default = None)
            form.integration_endpoint_action.data     = session.get("integration_endpoint_action", default = None)
            form.integration_endpoint_choice.data     = session.get("integration_endpoint_choice", default = None)
            form.integration_endpoint_ids.data        = session.get("integration_endpoint_ids", default = None)

            #Check if a return value was stored in the session from a previous POST request
            return_dictionary = session.get("console_return_value", default=None)

            #Render the page
            return render_template("console.html", form=form, return_dictionary=return_dictionary, title="Console")
        except Exception as e:
            db.session.rollback()
            abort(500)
   
    else:
        flash("First Add or Select a STEP system!", "warning")
        return redirect(url_for("core.systems"))







#The rest api page
@bp.route("/rest-api", methods=["GET", "POST"])
@login_required
def rest_api():
    if g.selected_system:
        form = RestAPIRequestForm()
        
        # This will hold any dynamic fields values input by the user for a specific path
        dynamic_values = {}

        #This IF block is to add the dynamic fields for specific request types to the main REST API form and create a new form to validate those fields
        # It's valid on form submission, so form validation is also part of this block
        if request.method == 'POST':
            # Savings inputs in session here in case of any errors in config so that user doesn't lose what they were doing
            request_type     = form.request_type.data
            request_endpoint = form.request_endpoint.data
            request_category = form.request_category.data
            request_path     = form.request_path.data
            request_body     = form.request_body.data

            session["rest_api_request_type"]      = request_type
            session["rest_api_request_endpoint"]  = request_endpoint
            session["rest_api_request_category"]  = request_category
            session["rest_api_request_path"]      = request_path
            session["rest_api_request_body"]      = request_body

            dynamic_value_list = re.findall(r"\{([^}]+)\}", request.form.get('request_path', ''))
            
            if dynamic_value_list:
                # Create a new Form that extends the existing REST API form
                class DynamicRestAPIRequestForm(RestAPIRequestForm):
                    pass
                
                # Append Each dynamic value to the form as it's own field that is MANDATORY
                for dynamic_value in dynamic_value_list:
                    setattr(DynamicRestAPIRequestForm, dynamic_value, StringField(dynamic_value, validators=[DataRequired()]))
                
                form = DynamicRestAPIRequestForm()
                
                # Populate dynamic_values dictionary to preserve inputs, if validation fails
                for dynamic_value in dynamic_value_list:
                    if dynamic_value in request.form:
                        dynamic_values[dynamic_value] = request.form[dynamic_value]
                
                
            
            if form.validate_on_submit():
                session["userid"]    = form.executing_user_id.data
                session["password"]  = form.executing_user_password.data
                session["context"]   = form.context_id.data
                session["workspace"] = form.workspace_id.data

                # Replace dynamic values in the path with values from the form
                for dynamic_value in dynamic_value_list:
                    field_data = getattr(form, dynamic_value).data
                    request_path = request_path.replace("{" + dynamic_value + "}", field_data)

                final_url = g.selected_system.system_url + request_endpoint + request_path

                params = {}
                if form.context_id.data:
                    params["context"] = form.context_id.data
                if form.workspace_id.data:
                    params["workspace"] = form.workspace_id.data

                session["rest_api_dynamic_values"] = dynamic_values
                session["rest_api_return_value"] = api_execute("rest-api", final_url, form.executing_user_id.data, form.executing_user_password.data, rest_request_type=request_type, rest_params=params, rest_body=request_body)

                #PRG pattern to avoid refresh page errors
                return redirect(url_for("api.rest_api"))


        #Set Default inputs for the form
        form.executing_user_id.data               = session.get("userid", default = g.selected_system.step_user_id)
        form.executing_user_password.data         = session.get("password", default = g.selected_system.step_user_password)
        form.context_id.data                      = session.get("context", default = g.selected_system.default_context)
        form.workspace_id.data                    = session.get("workspace", default = g.selected_system.default_workspace)

        form.request_type.data                    = session.get("rest_api_request_type", default = None) 
        form.request_endpoint.data                = session.get("rest_api_request_endpoint", default = None)
        form.request_category.data                = session.get("rest_api_request_category", default = None)
        form.request_path.data                    = session.get("rest_api_request_path", default = None)
        form.request_body.data                    = session.get("rest_api_request_body", default = None)
        dynamic_values                            = session.get("rest_api_dynamic_values", default = {})

        return_dictionary                         = session.get("rest_api_return_value", default = None)

        return render_template("rest-api.html", form = form, return_dictionary=return_dictionary, title="Rest API", dynamic_values=dynamic_values)
    
    else:
        flash("First Add or Select a STEP system!", "warning")
        return redirect(url_for("core.systems"))