from flask import g
import requests
from app import db
import sqlalchemy as sa
from app.models import System
import json
from bs4 import BeautifulSoup
# Use defusedxml to prevent XML vulnerabilities (XXE, XML Bombs)
import defusedxml.ElementTree as ET
from datetime import datetime, timezone, timedelta
from flask_moment import moment

"""
Healthcheck Utils
"""
#This method is used to parse the xml data returned by the 'Monitoring Sensors' method
def parseXMLResponse(inputXML):
    sensors = []
    try:
        outer_root = ET.fromstring(inputXML)
        long_text_element = outer_root.find('long-text')
        
        if long_text_element is not None and long_text_element.text:
            cdata_content = long_text_element.text.strip()
            escaped_content = cdata_content.replace('&', '&amp;')
            inner_root = ET.fromstring(escaped_content)
            for sensor_element in inner_root.findall('.//sensor'):
                sensors.append(sensor_element.attrib)
        return sensors
                
    except Exception as e:
        return [{"name": "Parse Error", "status": "Unable to Parse the Returned XML file : " + str(e)}]


#This function parses the sensor detail xml and converts it to a dictionary for webpage use
def append_to_list(return_dict, xml_data_element):
    for child in xml_data_element:
        name_value = None
        value_value = None
        
        if len(child) > 0:
            for grandchild in child:
                if grandchild.tag == "name":
                    name_value = grandchild.text

                elif grandchild.tag == "value":
                    value_value = grandchild.text

                else:
                    append_to_list(return_dict, child)

        else:
            name_value = child.tag
            value_value = child.text

        if name_value and value_value:
            formatted_value = value_value.strip().replace('\n', '<br/>')
            return_dict[name_value] = formatted_value


#This method is used to parse the sensors details xml input
def parse_details_xml(xml_string):
    try:
        root = ET.fromstring(xml_string)
        final_return_dict = {}
        append_to_list(final_return_dict, root)
        return final_return_dict
    except:
        final_return_dict = {
            "Message" : "<span class='text-danger'>Error while parsing the Sensor detail data. Please contact Admin</span>"
        }
        
    return final_return_dict


def parse_healthcheck_response(input_healthcheck_graphql_response, filter_timestamp):
    try:
        input_to_dictionary = json.loads(input_healthcheck_graphql_response)
        healthcheck_list = input_to_dictionary["data"]["healthChecks"]
        
        final_list_of_dictionaries = []

        for healthcheck in healthcheck_list:
            completed_at = int(healthcheck["completedAt"] / 1000.0)
            if completed_at >= filter_timestamp:
                time = datetime.fromtimestamp(completed_at, timezone.utc)
                
                healthcheck_dictionary = {
                    "ID" : healthcheck["ID"],
                    "name" : healthcheck["name"],
                    "category" : healthcheck["category"],
                    "issueCount" : healthcheck["issueCount"],
                    "severity" : healthcheck["severity"],
                    "time" : time,
                    "status" : healthcheck["status"], 
                    "type" : healthcheck["__typename"]
                }
                
                final_list_of_dictionaries.append(healthcheck_dictionary)

        if not final_list_of_dictionaries:
            final_list_of_dictionaries = "No healthchecks found for the specified time period"
        
        return final_list_of_dictionaries
    
    except Exception as e:
        return str(e)


"""
API Utils
"""
# Get the bearer token for selected method, either saved in the db, or requesting a new one
def get_bearer_token(user_id, user_password, force_refresh=False): 
    # Constructing return dictionary
    return_token_dictionary = {
        "tokenObtained" : False,
        "token"  : None,
        "additional_data": None
    }

    try:
        old_token_rejected_reason = None
        if not force_refresh:
            #Try to get existing bearer token from db
            existing_bearer_token = db.session.execute(sa.select(System.bearer_token).where(System.id==g.selected_system.id) ).scalar_one_or_none()
            
            #If token exists, check that it belongs to the current input user, if yes then return that and exit flow
            if existing_bearer_token:
                if existing_bearer_token["username"] == user_id and existing_bearer_token["password"] == user_password:
                    # Check how long ago token was generated, if it was more that one hour, means it expired and so request a new one
                    return_token_generation_time = datetime.fromisoformat(existing_bearer_token["generated"])
                    token_expiration_duration = g.api_bearer_token_ttl or 300
                    if (datetime.now(timezone.utc) - return_token_generation_time).total_seconds() < token_expiration_duration:
                        # If all good, return old token to be reused
                        return_token_dictionary["tokenObtained"] = True
                        return_token_dictionary["token"] = existing_bearer_token["token"]
                        return_token_dictionary["additional_data"] = "Used saved token from <span class='fw-semibold'> {} </span>".format(moment(return_token_generation_time).fromNow())
                        return return_token_dictionary
                    else:
                        old_token_rejected_reason = "Existing token in DB was older than set limit of {} seconds.".format(token_expiration_duration)
                else:
                    old_token_rejected_reason = "Existing token in DB was for a different user+password"       
            else:
                old_token_rejected_reason = "No existing token in DB"
        else:
            old_token_rejected_reason = "Force refreshed old token"


        # Flow to request a new token and save in DB against original credentials
        url = g.selected_system.system_url + "/auth/token"
        body = {
            "username" : user_id,
            "password" : user_password
        }
        headers = {
            "Content-Type": "application/json"
        }

        # Make the request
        response = requests.post(url, headers=headers, json=body)

        # If received good response, save and return it
        if response.status_code == 200:
            new_bearer_token = response.json()["accessToken"]
            
            return_token_dictionary["tokenObtained"] = True
            return_token_dictionary["token"] = new_bearer_token
            return_token_dictionary["additional_data"] = "Requested a new token - {}".format(old_token_rejected_reason)
            
            save_to_db_dictionary = {
                "username" : user_id,
                "password" : user_password,
                "token"    : new_bearer_token,
                "generated" : datetime.now(timezone.utc).isoformat()
            }

            g.selected_system.bearer_token = save_to_db_dictionary
            db.session.add(g.selected_system)
            db.session.commit()
        
        else:
            return_token_dictionary["additional_data"] = "Could not authenticate against the given credentials and system url, error code {}".format(response.status_code)
    
    except Exception as e:
        db.session.rollback()
        return_token_dictionary["additional_data"] = "Application error occured when trying to authenticate. Please contact admin."
    
    return return_token_dictionary


#This method executes the actual graphql query
def make_graphql_request(inputQuery, bearer_token):
    #Create return value dictionary with default status and details of request
    apiResponseDictionary = {
        "errorOccured" : True,
        "responseData" : ""
    }
    
    try:
        # Get default timeout set
        timeout = g.api_timeout or 60

        # Get URL of the system to make the request
        endpoint_url = g.selected_system.system_url + "/graphqlv2/graphql"

        #Request Headers
        headers = {
            "Authorization": "Bearer {}".format(bearer_token),
            "Content-Type": "application/json",
            "Accept": "application/graphql"
        }

        #Request Payload
        payload = {
            "query": inputQuery
        }

        response = requests.request("POST", endpoint_url, headers=headers, json=payload, timeout=timeout)

        #Check Response
        if response.status_code == 200:
            apiResponseDictionary["errorOccured"] = False
            try:
                apiResponseDictionary["responseData"] = json.dumps(response.json(), indent=4)
            except Exception:
                apiResponseDictionary["responseData"] = response.text
        else:
            apiResponseDictionary["responseData"] = "GraphQL Query execution failed - error code {}".format(response.status_code)
    
    #Timeout Error
    except requests.exceptions.Timeout:
        apiResponseDictionary["responseData"] = "Request Timed Out!"
    
    #Any other error
    except Exception as e:
        apiResponseDictionary["responseData"] = "Application Error occured when making the GraphQL call, please contact the ADMIN."
        
    #Final Function Return
    return apiResponseDictionary


#This method makes the actual rest api call and returns result based on input parameters
def make_rest_api_request(rest_request_type, rest_request_url, bearer_token, params, web_return=False, body=False):
       
    #Create return value dictionary with default status and details of request
    request_response_dictionary = {
        "errorOccured" : True,
        "responseData" : ""
    }

    #Make request
    try:
        timeout = g.api_timeout or 60
        
        #Request Headers
        headers = {
            "Authorization": "Bearer {}".format(bearer_token),
        }

        #The Main Request
        if rest_request_type in ['post', 'put', 'patch'] and body:
            headers["content-type"] = "application/json"
            parsed_json = json.loads(body)
            response = requests.request(rest_request_type, rest_request_url, headers=headers, params=params, timeout=timeout, json=parsed_json)
        else:
            response = requests.request(rest_request_type, rest_request_url, headers=headers, params=params, timeout=timeout)
        
        #Request succeded, set status as success and return json of response
        if response.status_code == 200:
            request_response_dictionary["errorOccured"] = False


            try:
                request_response_dictionary["responseData"] = response.json()
                if web_return:
                    request_response_dictionary["responseData"] = json.dumps(response.json(), indent=4)
            except Exception:
                request_response_dictionary["responseData"] = response.text

        elif response.status_code == 204:
            request_response_dictionary["errorOccured"] = False
            request_response_dictionary["responseData"] = "Success"
        
        elif response.status_code == 201:
            request_response_dictionary["errorOccured"] = False
            request_response_dictionary["responseData"] = "Success - Resource created on the system."

        else:
            request_response_dictionary["responseData"] = "Error code {} - {}".format(response.json()["httpStatus"], response.json()["message"])

        #Various errors that can occour
        # elif response.status_code == 400:
        #     request_response_dictionary["responseData"] = "Bad Request : Double check the Context and Workspace ID's. Alternatively, the configured user may not have privileges to perform the selected action."
        # elif response.status_code == 401:
        #     request_response_dictionary["responseData"] = "Unauthorized : Provided credentials are not valid on the selected system."
        # elif response.status_code == 403:
        #     request_response_dictionary["responseData"] = "Server Unreachable - The application cannot connect to the STEP system. This may indicate a whitelisting issue."
        # elif response.status_code == 404:
        #     request_response_dictionary["responseData"] = "Requested Resource not found - check the Request and any STEP Object ID's. Also make sure executing user has permission to access it."
        # elif response.status_code == 429:
        #     request_response_dictionary["responseData"] = "Too Many Requests - Client is limited to 100 requests per minute."
        # elif response.status_code == 500:
        #     request_response_dictionary["responseData"] = "Unexpected Error - Does the user have privilege to do the specified action?"
        # elif response.status_code == 503:
        #     request_response_dictionary["responseData"] = "Service Unavailable - Check if the system is available."
        # else:
        #     request_response_dictionary["responseData"] = "REST API execution failed - error code {}".format(str(response.status_code))
    
    # Timeout Error
    except requests.exceptions.Timeout:
        request_response_dictionary["responseData"] = "Request Timed Out!"

    # JSON body parse error
    except json.JSONDecodeError as e:
        request_response_dictionary["responseData"] = "Invalid json body passed."
    
    # Any other error
    except Exception as err:
        request_response_dictionary["responseData"] = "Application Error Occured when making the REST API call, please contact the Admin."

    #Final Function Return
    return request_response_dictionary


def api_execute(api_type, main_input, user_id, user_password, **rest_api_options):

    return_dictionary = {
        "header" : "<span class='text-danger'> API Execution Failed </span>",
        "data" : "",
        "error": True
    }

    try:
        # Try to obtain bearer token
        bearer_token_response = get_bearer_token(user_id, user_password)
        if bearer_token_response["tokenObtained"]:
            bearer_token = bearer_token_response["token"]
            
            if api_type == "rest-api":
                response = make_rest_api_request(rest_api_options["rest_request_type"], main_input, bearer_token, rest_api_options["rest_params"], web_return=True, body=rest_api_options["rest_body"])

            elif api_type == "graphql": 
                response = make_graphql_request(main_input, bearer_token)
            
            else:
                return_dictionary["data"] = "Invalid Request Type"
                return return_dictionary

            if not response["errorOccured"]:
                return_dictionary["header"] = "<span class='text-success'> API Execution Succeded </span>"
                return_dictionary["error"] = False
            return_dictionary["data"] = response["responseData"]
            
        else:
            # Return what error the bearer token obtaining method specified
            return_dictionary["data"] = bearer_token_response["additional_data"]
    
    except Exception:
        return_dictionary["data"] = "Application Error Occured when trying to parse the request, please contact the ADMIN."

    return return_dictionary



def console_execute(selected_option, user_id, user_password, context, workspace, integration_endpoint_type=None, integration_endpoint_action=None, integration_endpoint_choice=None, integration_endpoint_ids=None):
    try:
        #Default Return and other variables
        return_dictionary = {
            "header" : "<span class='text-danger'> API Call Failed </span>",
            "data" : ""
        }
        returnText = ""
        main_url = ""

        bearer_token_response = get_bearer_token(user_id, user_password)
        if bearer_token_response["tokenObtained"]:
            bearer_token = bearer_token_response["token"]            
        else:
            # Return what error the bearer token obtaining method specified
            return_dictionary["data"] = bearer_token_response["additional_data"]
            return return_dictionary

        #Root url of the system selected by the user
        system_url = g.selected_system.system_url

        #Most rest api requests are at this path. If any differ (eg. system restart), they will be overridden in that logical block
        path_url = "/restapiv2"

        
        #Optional query parameters, will be set if they are input by the user
        params = {}
        if context:
            params["context"] = context
        if workspace:
            params["workspace"] = workspace
        
        
        #Make Server Restart Request on selected systems
        if selected_option == "server_restart":
            path_url = "/system-management"
            main_url = "/step/restart"
            
            #Construct Full API call url
            url = system_url + path_url + main_url

            response = make_rest_api_request("POST", url, bearer_token, params)

            if response["errorOccured"]:
                return_dictionary["data"] = response["responseData"]
            else:
                return_dictionary["header"] = "<span class='text-success'> Success </span>"
                return_dictionary["data"] = "Server Restart Initiated..."



        #Make System Details Request on selected systems
        elif selected_option == "system_details":
            path_url = ""
            main_url = "/about/step"

            #Construct Full API call url
            url = system_url + path_url + main_url

            response = make_rest_api_request("GET", url, bearer_token, params)

            if response["errorOccured"]:
                return_dictionary["data"] = response["responseData"]
            
            else:
                returnText = "<div class='table-responsive'><table class='table table-hover'> <tbody>"
                
                soup = BeautifulSoup(response["responseData"], "html.parser")
                values = soup.find_all("div", {"class": "about-entry"})
                for value in values:
                    value_string = str(value)
                    if ":" in value_string:
                        returnText += "<tr class='text-start'> <td> {} </td><td> {} </td> </tr>".format(str(value).split(":")[0], str(value).split(":")[1])
                
                #Fetch License Components
                license_components = ""
                main_url_license_components = "/about/version"
                url_license_components = system_url + path_url + main_url_license_components
                license_components_response = make_rest_api_request("GET", url_license_components, bearer_token, params)
                
                
                if license_components_response["errorOccured"]:
                    license_components = "Unable to Fetch"
                else:
                    soup = BeautifulSoup(license_components_response["responseData"], "html.parser")
                    version_sections = soup.find_all("div", class_="version-section")
                    second_section = version_sections[1]
                    values = second_section.find_all("div", class_="version-value")
                    for value in values:
                        license_components += str(value)

                returnText += "<tr class='text-start'> <td> License-enabled Components </td><td> {} </td> </tr>".format(license_components)
                returnText += "</tbody></table></div>"

                return_dictionary["header"] = "<span class='text-success'> System Details Fetched </span>"
                return_dictionary["data"] = returnText


        #Validate Credentials
        elif selected_option == "validate_credentials":
            main_url = "/users/" + user_id
            url = system_url + path_url + main_url

            response = make_rest_api_request("GET", url, bearer_token, params)

            if response["errorOccured"]:
                return_dictionary["data"] = response["responseData"]
            else:
                message = response["responseData"]
                returnText += "<div class='table-responsive'><table class='table table-hover'> <thead> <tr class='text-start'> <th> Property </th> <th> Value </th> </tr> </thead> <tbody>"
                returnText += "<tr class='text-start'> <td> Username </td><td>" + message['name'] + "</td> </tr>"
                returnText += "<tr class='text-start'> <td> Email </td><td>" + str(message['email']) + "</td> </tr>"
                returnText += "<tr class='text-start'> <td> Part of Groups </td><td>" + str(message["userGroups"]) + "</td> </tr>"
                returnText += "</tbody></table> </div>"

                return_dictionary["header"] = "<span class='text-success'> Credentials Successfully Validated. </span>"
                return_dictionary["data"] = returnText



        elif selected_option == "integration_endpoint_action":       
            #Common Error Scenarios
            if integration_endpoint_choice == "specified" and not integration_endpoint_ids:
                return_dictionary["data"] = "Please provide ID's for the selected action."
            
            elif not integration_endpoint_type or not integration_endpoint_action:
                return_dictionary["data"] = "Type and Action are Mandatory"

            elif integration_endpoint_type == "giep" and integration_endpoint_action == "invoke":
                return_dictionary["data"] = "Cannot invoke Gateway Integration Endpoints"
            
            else:
                #For OIEP Functions
                if integration_endpoint_type == "oiep":
                    main_url = "/outbound-integration-endpoints"
                    step_object_type_name = "Outbound Endpoints"
                #For IIEP Functions
                elif integration_endpoint_type == "iiep":
                    main_url = "/inbound-integration-endpoints"
                    step_object_type_id = "IIEP"
                    step_object_type_name = "Inbound Endpoints"
                
                #For GIEP Functions
                elif integration_endpoint_type == "giep":
                    main_url = "/gateway-integration-endpoints"
                    step_object_type_name = "Gateway Endpoints"
                
                #For Event Processor Functions
                elif integration_endpoint_type == "ep":
                    main_url = "/event-processors"
                    step_object_type_name = "Event Processors"
                
                #Construct the Call URL
                url = system_url + path_url + main_url

                
                #The list used to store specified ID's if given
                specified_id_array = None
                if integration_endpoint_choice == "specified":
                    specified_id_array = [item.strip() for item in integration_endpoint_ids.split(';')]

                
                
                #Fetch name and ID of all objects of specified type from the selected system
                base_response = make_rest_api_request("GET", url, bearer_token, params)

                if base_response["errorOccured"]:
                    return_dictionary["data"] = base_response["responseData"]
                
                else:
                    #Fetch Basic Details Block
                    if integration_endpoint_action == "list":
                        returnText = "<div class='table-responsive'><table class='table table-hover'> <thead> <tr class='text-start'> <th> ID </th> <th> Name </th> </tr> </thead> <tbody>"
                        
                        message = base_response["responseData"]
                        
                        if len(base_response["responseData"]) > 0:
                            for entry in message:
                                #If only specified info requested, filter output
                                if integration_endpoint_choice == "specified":
                                    if entry["id"] in specified_id_array:
                                        returnText += "<tr class='text-start'> <td>" + entry["id"] + "</td><td>" + entry["name"] + "</td> </tr>"
                                else:
                                    returnText += "<tr class='text-start'> <td>" + entry["id"] + "</td><td>" + entry["name"] + "</td> </tr>"
                            
                            returnText += "</tbody></table></div>"
                            return_dictionary["header"] = "<span class='text-success'> Finished 'Basic details fetch' operation for {} {} </span>".format(integration_endpoint_choice, step_object_type_name)
                            return_dictionary["data"] = returnText
                        else:
                            return_dictionary["data"] = "<span class='text-danger'>Found no objects of selected type in the system. If this sounds wrong, check if the configured user has the privileges to view them!</span>"


                    #Fetch Advanced Details Block
                    elif integration_endpoint_action == "list_detailed":
                        #Construct list based on if all or only specified ID's details are needed
                        if integration_endpoint_choice == "specified":
                            working_list_of_ids = specified_id_array
                        else:
                            working_list_of_ids = [entry["id"] for entry in base_response["responseData"]]
                        
                        
                        returnText = "<div class='table-responsive'> <table class='table table-hover'> <thead> <tr class='text-start'>"
                        
                        #Create tabular structure based on each type's available attributes in the response
                        if integration_endpoint_type == "ep":
                            returnText += "<th> ID </th> <th> Name </th>  <th> Configured User </th> <th> Status </th>"
                        elif integration_endpoint_type == "giep":
                            returnText += "<th> ID </th> <th> Name </th>  <th> Description </th> <th> Status </th>"
                        else:
                            returnText += "<th> ID </th> <th> Name </th>  <th> Description </th> <th> Configured User </th> <th> Status </th>"
                        
                        returnText += "</tr> </thead> <tbody>"

                        if len(working_list_of_ids) > 0 :
                            #Run specified operation on each entry
                            for step_object_id in working_list_of_ids:       
                                #Fetch Name, Description and Configured User for all ID's in List
                                main_url_for_details = main_url + "/{}".format(step_object_id)
                                url = system_url + path_url + main_url_for_details
                                details_response = make_rest_api_request("GET", url, bearer_token, params)
                                
                                if details_response["errorOccured"]:
                                    step_object_name = "Unknown"
                                    step_description = "Unknown"
                                    configured_user = "Unknown"

                                else:
                                    step_object_name = details_response["responseData"]["name"]
                                    
                                    #Event processors don't have description
                                    if integration_endpoint_type != "ep":
                                        step_description = details_response["responseData"]["description"]
                                    
                                    #Gateway endpoints don't have a configured user
                                    if integration_endpoint_type != "giep":
                                        configured_user = details_response["responseData"]["user"]                    

                                #Fetch status for all ID's in List
                                main_url_for_status = main_url + "/{}/status".format(step_object_id)
                                url = system_url + path_url + main_url_for_status
                                is_enabled_response = make_rest_api_request("GET", url, bearer_token, params)
                                
                                if is_enabled_response["errorOccured"]:
                                    status = "unknown"
                                else:
                                    status = is_enabled_response["responseData"]["status"]

                                    if status == "enabled":
                                        status_dot = "<i class='bi bi-dot text-success fs-1' title='{}'></i>".format(status.title())
                                    elif status == "disabled":
                                        status_dot = "<i class='bi bi-dot text-warning fs-1' title='{}'></i>".format(status.title())
                                    elif status == "failed":
                                        status_dot = "<i class='bi bi-dot text-danger fs-1' title='{}'></i>".format(status.title())
                                    else:
                                        status_dot = "<i class='bi bi-dot text-secondary fs-1' title='{}'></i>".format(status.title())


                                if integration_endpoint_type == "ep":
                                    returnText += "<tr scope='row' class='text-start'> <td> {} </td>  <td> {} </td> <td> {} </td> <td> {} </td> </tr>".format(step_object_id,step_object_name, configured_user, status_dot)
                                elif integration_endpoint_type == "giep":
                                    returnText += "<tr scope='row' class='text-start'> <td> {} </td>  <td> {} </td> <td> {} </td> <td> {} </td> </tr>".format(step_object_id,step_object_name,step_description, status_dot)
                                else:
                                    returnText += "<tr scope='row' class='text-start'> <td> {} </td>  <td> {} </td> <td> {} </td> <td> {} </td> <td> {} </td> </tr>".format(step_object_id,step_object_name,step_description, configured_user, status_dot)

                            returnText += "</tbody></table></div>"
                            return_dictionary["header"] = "<span class='text-success'> Finished 'Advanced details fetch' operation for {} {} </span>".format(integration_endpoint_choice, step_object_type_name)
                            return_dictionary["data"] = returnText
                        else:
                            return_dictionary["data"] = "<span class='text-danger'>Found no objects of selected type in the system. If this sounds wrong, check if the configured user has the privileges to view them!</span>"
                    
                    elif integration_endpoint_action == "invoke" or integration_endpoint_action == "enable" or integration_endpoint_action == "disable":
                        #Construct list based on if all or only specified ID's action is needed
                        if integration_endpoint_choice == "specified":
                            working_list_of_ids = specified_id_array
                        else:
                            working_list_of_ids = [entry["id"] for entry in base_response["responseData"]]

                        returnText = "<table class='table table-hover'> <thead> <tr class='text-start'> <th> ID </th> <th> Result </th> </tr> </thead> <tbody>"
                        
                        for step_id in working_list_of_ids:
                            main_url_temp = main_url + "/{}/{}".format(step_id, integration_endpoint_action)
                            url = system_url + path_url + main_url_temp
                            
                            response = make_rest_api_request("POST", url, bearer_token, params)
                            
                            if response["errorOccured"]:
                                returnText += "<tr scope='row' class='text-start'> <td> {} </td> <td> <span class='text-danger'> {} </span> </td> </tr>".format(step_id, response["responseData"])
                            else:
                                output_message = response["responseData"]
                                if not output_message:
                                    output_message = "Success"
                                returnText += "<tr scope='row' class='text-start'> <td> {} </td> <td> <span class='text-success'> {} </span> </td> </tr>".format(step_id, output_message)
                        
                        returnText += "</tbody></table>"
                        return_dictionary["header"] = "<span class='text-success'> Finished running selected operation on {} {} </span>".format(integration_endpoint_choice, step_object_type_name)
                        return_dictionary["data"] = returnText

                    else:
                        return_dictionary["data"] = "Invalid Action Type selected!"


    except Exception as e:
        return_dictionary["data"] = "Application Error Occured when parsing the REST API data, please contact the ADMIN."

    return return_dictionary
