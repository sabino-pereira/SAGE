from flask import render_template, flash, redirect, url_for, abort, g, request
from flask_login import current_user, login_user, logout_user
from app.auth.forms import LoginForm, RegistrationForm
from app.core.core_utils import clear_session_variables
from app.auth import bp
import sqlalchemy as sa
from app.models import User, Link, PageVisit
from app import db
from urllib.parse import urlsplit
from datetime import datetime, timezone


#The login page
@bp.route("/login", methods=["GET", "POST"])
def login():
    #If already logged in, send to homepage
    if current_user.is_authenticated:
        flash("Already logged in!")
        return redirect(url_for("core.home"))
    
    #Login form creation and check on submit (POST method)
    form = LoginForm()
    if form.validate_on_submit():

        try:
            #Check for existing user using both username and email
            user = db.session.scalar(
                sa.select(User).where(sa.or_(User.username == form.username.data, User.email == form.username.data))
            )

            #Means both checks failed OR password is invalid
            if user is None or not user.check_password(form.password.data):
                flash("Invalid Username or Password!")
                return redirect(url_for("auth.login"))

            
            #Means correct password. So show message and login user
            #flash("Welcome {}!".format(user.username.title()))
            login_user(user, remember=form.remember_me.data)
            
            
            visit = db.session.scalar(sa.select(PageVisit).where(PageVisit.user_id == user.id).where(PageVisit.page_name == "Login"))
            if visit:
                visit.visit_count += 1
                visit.last_visited = datetime.now(timezone.utc)
            else:
                visit = PageVisit(user_id=user.id, page_name="Login", visit_count=1, last_visited=datetime.now(timezone.utc))
            
            db.session.add(visit)
            db.session.commit()


            #Send to Home Page or Next Page
            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('core.home')
            return redirect(next_page)
        except Exception:
            #In case of exception, show error page
            abort(500)

    #Default Load Page (GET method)
    return render_template("login.html", form=form, title="Login")


#The User Registration page
@bp.route("/register", methods=["GET", "POST"])
def register():
    #Check is user has allowed registraion on this server
    if not g.registration_allowed:
        flash("Registration not allowed!", "danger")
        return redirect(url_for("core.home"))

    else:
        #If already logged in, send to homepage
        if current_user.is_authenticated:
            flash("Cannot register when logged in!", "warning")
            return redirect(url_for("core.home"))
        
        #Registration form creation and check on submit (POST method)
        form = RegistrationForm()
        
        create_admin_user = False
        user_count = db.session.scalars(sa.select(User)).first()
        if not user_count:
            create_admin_user = True
        
        if form.validate_on_submit():
            try:
                #Create new user object and add to database (user already exists check is done by the form itself)
                new_user = User(username=form.username.data, email=form.email.data)
                if create_admin_user:
                    new_user.user_role = "admin"
                new_user.set_password(form.password.data)
                db.session.add(new_user)
                db.session.commit()

                #Add default quick access links for user on registration
                default_links = [
                    {"name" : "Stibo Community", "url" : "https://community.stibosystems.com"},
                    {"name" : "Stibo Blog", "url" : "https://www.stibosystems.com/blog"},
                    {"name" : "Support Center", "url" : "https://supportcenter.app.stibosystems.com"},
                    {"name" : "Stibo SaaS Status Hub", "url" : "https://statushub.mdm.stibosystems.com"},
                    {"name" : "STEP WebUI Design System", "url" : "https://webuidesignsystem.stibosystems.com/6f6a47546/p/14f87a-step-web-ui-design-system"},
                    {"name" : "STEP Documentation", "url" : "https://doc.stibosystems.com/doc/version/latest/web/content/homepage.html"},
                ]
                
                for link_object in default_links:
                    new_link = Link(link_name = link_object["name"], link_url = link_object["url"])
                    new_link.user_id = new_user.id
                    db.session.add(new_link)
                    
                db.session.commit()
                
                #Show success message and route to login pages
                flash("Created account for user {}. You can now login".format(form.username.data), "success")
                return redirect(url_for('auth.login'))
            
            except Exception as e:
                #In case of error, rollback db, and redirect to error page
                db.session.rollback()
                abort(500)

        #Default Load Page (GET method)
        return render_template("register.html", form=form, create_admin_user=create_admin_user, title="Register")




@bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        clear_session_variables()
        logout_user()
    return redirect(url_for('core.home'))