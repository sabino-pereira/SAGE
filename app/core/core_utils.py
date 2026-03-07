from flask import session
from flask_login import current_user
from app import db
import sqlalchemy as sa
from app.models import System
import csv, io, json


#This method will clear variables from session except the ones passes as a list argument
def clear_session_variables(exception_list=[]):
    all_session_variables_list = [
        "userid",
        "password",
        "context",
        "workspace",
        "console_return_value",
        "integration_endpoint_type",
        "integration_endpoint_action",
        "integration_endpoint_choice",
        "integration_endpoint_ids",
        "graphql_old_query",
        "graphql_return_value",
        "rest_api_return_value",
        "rest_api_request_type",
        "rest_api_request_endpoint",
        "rest_api_request_category",
        "rest_api_request_path",
        "rest_api_request_body",
        "rest_api_dynamic_values",
        "healthcheck_return_value",
        "healthcheck_input_number",
        "healthcheck_time_unit"
    ]
    for variable in all_session_variables_list:
        if variable not in exception_list:
            if variable in session:
                session.pop(variable)



#This method is used to return the System object that the user has currently selected.
def get_selected_system_from_db():
    system = None
    if not current_user.is_anonymous:
        if current_user.selected_system_id:
            selected_system = db.session.scalar(sa.Select(System).where(System.id == current_user.selected_system_id))
            system = selected_system    
    return system



def tools_utils(action_type, input):
    returnDictionary = {         
        "action_type" : action_type,         
        "message" : ""     
    }      
    try:         
        #Convert csv list of ip's and descriptions to STEP self service portal json format         
        if action_type == "c2j":             
            csv_file_like_object = io.StringIO(input)             
            delimiter = csv.Sniffer().sniff(input).delimiter             
            csvreader = csv.reader(csv_file_like_object, delimiter=delimiter)              
            
            first_row = next(csvreader)
            if len(first_row) != 2:
                returnDictionary["message"] = "<span class='text-danger'>Invalid CSV format, please click the '?' button above for details.</span>"
            
            else:
                csv_file_like_object.seek(0)
                final_json = []         
                for row in csvreader:                 
                    ip = row[0]                 
                    description = row[1]                 
                    final_json.append({"ip": ip, "description": description})              
                    returnDictionary["message"] = json.dumps(final_json)          
        
        #Convert json ip data exported from self service portal in a table         
        elif action_type == "j2c":             
            loaded_data = json.loads(input)             
            return_string = "<table class='table table-hover table-sm'> <thead> <tr class='text-start'> <th scope='col'> IP-Address </th> <th> Description </th></tr> </thead> <tbody class='table-group-divider'>"              
            for entry in loaded_data:                 
                return_string += "<tr class='text-start'><td>{}</td><td>{}</td></tr>".format(entry["ip"], entry["description"])             
                            
                returnDictionary["message"] = return_string          
            return_string += "</tbody> </table>"
        else:             
            returnDictionary["message"] = "<span class='text-danger'>Invalid Action Type Selected</span>"      
    
    except Exception as e:         
        returnDictionary["message"] = "<span class='text-danger'>Error Processing Data!</span>"      
        
    return returnDictionary