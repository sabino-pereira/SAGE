from flask import render_template, flash, redirect, url_for, g, session, abort, request
from flask_login import login_required, current_user
from app.core import bp
import requests
from app.core.core_utils import clear_session_variables, tools_utils
from app.core.forms import AddSystemForm, EditSystemForm, DeveloperToolsForm, AddLinkForm, DeleteForm
from app.models import System, Link, PageVisit, User
from urllib.parse import urlparse
import sqlalchemy as sa
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from app import db


#The homepage
@bp.route("/", methods=["GET", "POST"])
@bp.route("/home", methods=["GET", "POST"])
def home():
    if current_user.is_anonymous:
        return render_template("landing.html")

    #Initiate and check if Quick Access Links form was submitted.
    form = AddLinkForm()
    if form.submit.data and form.validate():
        try:
            #Check how many links user has already added
            existing_links_count = db.session.scalar(sa.select(sa.func.count()).select_from(Link).filter(Link.user_id == current_user.id))
            max_allowed_links = g.max_quick_access_links or 20
            
            if existing_links_count < max_allowed_links:
                #Create new Link object and add it to the database
                new_link = Link(link_name = form.link_name.data, link_url = form.link_url.data)
                new_link.user_id = current_user.id
                db.session.add(new_link)
                db.session.commit()
            
                flash("Added new Link: {} -> {}".format(form.link_name.data, form.link_url.data), "success")
            else:
                flash("You can only add a maximum of {} Quick Access Links!".format(max_allowed_links), "warning")
            
            return redirect(url_for('core.home'))

        except Exception:
            db.session.rollback()
            abort(500)

    #Fetch all links owned by current user to render on page
    all_links = list(db.session.scalars(sa.select(Link).filter(Link.user_id == current_user.id)))
    delete_form = DeleteForm()
    return render_template("home.html", form=form, all_links=all_links, delete_form=delete_form)



#Delete Link Route
@bp.route("/delete-link/<int:link_id>", methods=["POST"])
@login_required
def delete_link(link_id):
    form = DeleteForm()
    if form.validate_on_submit():
        result_dictionary = current_user.delete_link(link_id)
        flash(result_dictionary["response"], result_dictionary["status"])
    return redirect(url_for('core.home'))




"""
System Management Routes
"""
#The system-management page, allowing to View, Add, and Delete systems.
@bp.route("/systems", methods=["GET", "POST"])
@login_required
def systems():    
    #Initialize the form
    form = AddSystemForm()
    form_edit = EditSystemForm()
    form_delete = DeleteForm()
    
    # If Add system form submitted
    if form.submit.data and form.validate():
        try:
            #Check how many systems user has already added
            existing_systems_count = db.session.scalar(sa.select(sa.func.count()).select_from(System).filter(System.user_id == current_user.id))
            max_allowed_systems = g.max_systems or 20
            
            if existing_systems_count < max_allowed_systems:
                #Convert input system url to base domain with https at the start, this is just to cleanse the url if needed
                system_url = "https://" + str(urlparse(form.system_url.data).netloc)
                
                #Create new system object and add it to the database
                new_system = System(system_name = form.system_name.data, system_url = system_url, system_type = form.system_type.data, deployment_type=form.deployment_type.data, step_user_id = form.step_user_id.data, step_user_password = form.step_user_password.data, default_context = form.default_context.data, default_workspace = form.default_workspace.data)
                new_system.user_id = current_user.id
                db.session.add(new_system)
                db.session.commit()
                
                flash("Added new System: {} -> {}".format(form.system_name.data, system_url), "success")
            else:
                flash("You can only add a maximum of {} Systems!".format(max_allowed_systems), "warning")
            
            return redirect(url_for('core.systems'))

        except Exception:
            db.session.rollback()
            abort(500)

    # If edit system form submitted
    if form_edit.edit_submit.data and form_edit.validate():
        try:
            #Convert input system url to base domain with https at the start, this is just to cleanse the url if needed
            new_system_url = "https://" + str(urlparse(form_edit.edit_system_url.data).netloc)
            
            #Create new system object and add it to the database
            existing_system = db.session.scalar(sa.select(System).where(System.id == form_edit.edit_system_id.data, System.user_id == current_user.id))
            
            if existing_system:
                existing_system.system_name = form_edit.edit_system_name.data
                existing_system.system_url = new_system_url
                existing_system.system_type = form_edit.edit_system_type.data
                existing_system.deployment_type = form_edit.edit_deployment_type.data
                existing_system.step_user_id = form_edit.edit_step_user_id.data
                existing_system.step_user_password = form_edit.edit_step_user_password.data
                existing_system.default_context = form_edit.edit_default_context.data
                existing_system.default_workspace = form_edit.edit_default_workspace.data

                db.session.add(existing_system)
                db.session.commit()
                flash("System Successfully Edited", "success")
            else:
                flash("System not found or you don't have permission to edit it.", "danger")

            return redirect(url_for('core.systems'))

        except Exception:
            db.session.rollback()
            abort(500)

    #Fetch all systems owned by current user to render on page
    all_systems = list(db.session.scalars(sa.select(System).filter(System.user_id == current_user.id)))

    return render_template("systems.html", form=form, form_edit=form_edit,form_delete=form_delete, systems=all_systems, title="Systems")



#Select System Route
@bp.route("/select-system/<int:system_id>", methods=["POST"])
@login_required
def select_system(system_id):
    clear_session_variables()
    result_dictionary = current_user.select_system(system_id)
    flash(result_dictionary["response"], result_dictionary["status"])
    return redirect(url_for('core.systems'))


#Delete System Route
@bp.route("/delete-system/<int:system_id>", methods=["POST"])
@login_required
def delete_system(system_id):
    clear_session_variables()
    form = DeleteForm()
    if form.validate_on_submit():
        result_dictionary = current_user.delete_system(system_id)
        flash(result_dictionary["response"], result_dictionary["status"])
    return redirect(url_for('core.systems'))



#Fetch and return System details from DB (AJAX)
@bp.route("/fetch-system-details", methods=["POST"])
@login_required
def fetch_system_details():
    #Default return values
    returnDictionary = {
        "date": None,
        "content": None
    }
    
    if g.selected_system:
        # Fetched stored date and content from the DB
        if g.selected_system.details_fetched_date:
            returnDictionary["date"] = g.selected_system.details_fetched_date
        if g.selected_system.details_json_string:
            returnDictionary["content"] = g.selected_system.details_json_string   

    return returnDictionary
    


#System Details Live refresh, save in db, and return route (AJAX)
@bp.route("/refresh-system-details", methods=["POST"])
@login_required
def refresh_system_details():
    #Default return values
    returnDictionary = {
        "date": None,
        "content": None
    }

    #Try and make api call to fetch data, then parse and store it in the DB along with time, and return dictionary with values.
    try:
        user_id = g.selected_system.step_user_id
        user_password = g.selected_system.step_user_password

        if user_id and user_password:
            url = g.selected_system.system_url + "/about/step"
            auth=(user_id, user_password)
            
            response = requests.request("GET", url, auth=auth, timeout=g.api_timeout)

            if response.status_code == 200:
                value_dictionary = {}
                time_now = datetime.now(timezone.utc)

                soup = BeautifulSoup(response.text, "html.parser")
                values = soup.find_all("div", {"class": "about-entry"})
                for value in values:
                    value_string = value.get_text()
                    if ":" in value_string:
                        step_key = str(value_string).split(":")[0].strip().replace(" ","_")
                        step_value = str(value_string).split(":")[1].strip()
                        value_dictionary[step_key] = step_value

                
                
                g.selected_system.details_fetched_date = time_now
                g.selected_system.details_json_string = value_dictionary  
                db.session.add(g.selected_system)
                db.session.commit()

                returnDictionary["date"] = g.selected_system.details_fetched_date
                returnDictionary["content"] = g.selected_system.details_json_string
       
    except Exception:
        db.session.rollback()

    return returnDictionary






"""
Other Routes
"""
#Developer Tools Page
@bp.route("/tools", methods=["GET", "POST"])
def tools():
    form = DeveloperToolsForm()
    return_dictionary = None

    if form.validate_on_submit():
        return_dictionary = tools_utils(form.action_type.data, form.input_text.data)
    
    return render_template("tools.html", form=form, return_dictionary=return_dictionary, title="Tools")



#Reset Developer Tools Page Route
@bp.route("/reset-tools")
def reset_tools():
    return redirect(url_for("core.tools"))






#The Pro Tips page
@bp.route("/tips")
def tips():
    return render_template("tips.html", title="Pro Tips")





"""
Admin Routes
"""
@bp.route("/admin", methods=["GET", "POST"])
def admin():
    #Only allow for logged in 'Admin' users
    if current_user.is_anonymous or current_user.user_role.name != "admin":
        flash("You are not privileged to perform that action!", "danger")
        return redirect(url_for("core.home"))

    #Server IP
    try:
        ip_response = requests.get("http://checkip.amazonaws.com", timeout=2)
        ip =  ip_response.text
    except requests.exceptions.RequestException as e:
        ip =  "Unable to Fetch IP"

    #Get tab page name from request (defined in admin.html), default is users tab.
    tab = request.args.get("tab", "summary")
    #Get page number from request if it's defined, default is 1
    page = request.args.get("page", 1, type=int)
    per_page = 10

    #Database data dictionary
    data = {
        "users": None,
        "systems": None,
        "links": None,
        "visits": None
    }

    data_stats = {
        "users": 0,
        "systems": 0,
        "links": 0,
        "visits": 0
    }

    # Fetch only the data for the active tab using pagination
    if tab == "users":
        data["users"]      = db.paginate(sa.select(User), page=page, per_page=per_page)
    elif tab == "systems":
        data["systems"]    = db.paginate(sa.select(System), page=page, per_page=per_page)
    elif tab == "links":
        data["links"]      = db.paginate(sa.select(Link), page=page, per_page=per_page)
    elif tab == "visits":
        data["visits"]     = db.paginate(sa.select(PageVisit), page=page, per_page=per_page)
    elif tab == "summary":
        data_stats["users"]      = db.session.scalar(sa.select(sa.func.count()).select_from(User))
        data_stats["systems"]    = db.session.scalar(sa.select(sa.func.count()).select_from(System))
        data_stats["links"]      = db.session.scalar(sa.select(sa.func.count()).select_from(Link))
        data_stats["visits"]     = db.session.scalar(sa.select(sa.func.count()).select_from(PageVisit))


    form_delete = DeleteForm()
    return render_template("admin.html",form_delete=form_delete, tab=tab, data=data, data_stats=data_stats, ip=ip)


@bp.route("/admin/delete/<string:object_type>/<int:object_id>", methods=["POST"])
@login_required
def admin_delete_item(object_type, object_id):
    form = DeleteForm()
    if form.validate_on_submit():

        if current_user.user_role.name != "admin":
            flash("You are not privileged to perform that action!", "danger")
            return redirect(url_for("core.home"))

        # Object type to DB Model Dictionary
        models = {
            "user": User,
            "system": System,
            "link": Link,
            "visit": PageVisit
        }

        if object_type in models:
            #Don't allow to delete self user
            if object_type == "user" and object_id == current_user.id:
                flash("You cannot delete your own user account!", "danger")
            else:
                #Query for the object in the database
                object = db.session.get(models[object_type], object_id)
                if object:
                    try:
                        db.session.delete(object)
                        db.session.commit()
                        flash(f"{object_type.capitalize()} deleted successfully.")
                    
                    except Exception as e:
                        db.session.rollback()
                        flash("Error deleting {}.".format(object_type.capitalize()), "danger")
                else:
                    flash("Object not found.", "danger")
        else:
            flash("Invalid operation.", "danger")

        # Redirect back to the correct tab
    return redirect(url_for("core.admin", tab=object_type + "s"))