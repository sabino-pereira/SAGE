from flask import flash, abort
from flask_login import UserMixin
import sqlalchemy as sa
import sqlalchemy.orm as orm
from typing import Optional, List
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from app import db, login


#Loader function required by flask login to work
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


#For User Role
class User_Role(enum.Enum):
    admin    = "Admin"
    user     = "User"

#The User class, representing the user using the application
class User(UserMixin, db.Model):
    #Mandatory User Details
    id:            orm.Mapped[int]           = orm.mapped_column(primary_key=True)
    username:      orm.Mapped[str]           = orm.mapped_column(sa.String(length=10), index=True, unique=True)
    email:         orm.Mapped[str]           = orm.mapped_column(sa.String(length=254), index=True, unique=True)
    password_hash: orm.Mapped[str]           = orm.mapped_column(sa.String(length=256))
    user_role:     orm.Mapped[User_Role]     = orm.mapped_column(sa.Enum(User_Role, name="user_role_enum", create_constraint=True), index=True, default="user")
    

    #Optional User Details, selected system is the system the user wants to work on from the list of all systems
    user_last_active:   orm.Mapped[datetime]           = orm.mapped_column(default=lambda: datetime.now(timezone.utc))
    selected_system_id: orm.Mapped[Optional[int]]      = orm.mapped_column(sa.Integer())

    #Relationship between a User and added Systems, here 'System' class is passed as a string because it is defined later on in the code.
    systems: orm.Mapped[List["System"]] = orm.relationship(back_populates="user", cascade="all, delete-orphan")

    #Relationship between a User and added links, here 'Link' class is passed as a string because it is defined later on in the code.
    links: orm.Mapped[List["Link"]] = orm.relationship(back_populates="user", cascade="all, delete-orphan")

    #Relationship between a User and Page Visits, here 'PageVisit' class is passed as a string because it is defined later on in the code.
    page_visits: orm.Mapped[List["PageVisit"]] = orm.relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return "My usernam is {}. Reach me at {}".format(self.username.title(), self.email)
    
    #Function to update password hash when password is set
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    #Function to check if input password matches set password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    #Function to update user's last active timestamp
    def update_last_active(self):
        try:
            # Only update if more than 60 seconds have passed since the last update
            if not self.user_last_active or (datetime.now(timezone.utc) - self.user_last_active.replace(tzinfo=timezone.utc)).total_seconds() > 60:
                self.user_last_active = datetime.now(timezone.utc)
                db.session.commit()
        except Exception:
            db.session.rollback()

    #Function to change user's selected system
    def select_system(self, system_id):
        try:
            return_dictionary = {
                "status" : "success",
                "response" : ""
            }

            #If target system is selected system, de-select it.
            if self.selected_system_id == system_id:
                self.selected_system_id = None
                db.session.commit()
                return_dictionary["response"] = "De-selected system."
            else:
                #Query db for system, making sure current user owns the system
                system_to_select = db.session.scalar(
                    sa.select(System).where(System.id == system_id, System.user_id == self.id)
                )

                #If system exists, select it and flash a message
                if system_to_select:
                    self.selected_system_id = system_id
                    db.session.commit()
                    return_dictionary["response"] = "Selected system: {}".format(system_to_select.system_name)

                else:
                    return_dictionary["status"] = "danger"
                    return_dictionary["response"] = "System not found or you don't have permission to access it."
            return return_dictionary
         
        except Exception:
            # Rollback any database staged changes and throw a 500 error
            db.session.rollback()
            abort(500)


    
    #Function to delete a system
    def delete_system(self, system_id):
        try:
            return_dictionary = {
                "status" : "success",
                "response" : ""
            }

            #Query db for system, making sure current logged in user owns the system
            system_to_delete = db.session.scalar(
                sa.select(System).where(System.id == system_id, System.user_id == self.id)
            )

            #If system exists, delete it. If this system is the selected one, also clear the selection from user table
            if system_to_delete:
                if self.selected_system_id == system_to_delete.id:
                    self.selected_system_id = None
                db.session.delete(system_to_delete)
                db.session.commit()
                return_dictionary["response"] = "System: {} has been deleted.".format(system_to_delete.system_name)
            else:
                return_dictionary["status"] = "danger"
                return_dictionary["response"] = "System not found or you don't have permission to access it."
            
            return return_dictionary

        except Exception:
            # Rollback any database staged changes and throw a 500 error
            db.session.rollback()
            abort(500)



    #Function to delete a link
    def delete_link(self, link_id):
        try:
            return_dictionary = {
                "status" : "success",
                "response" : ""
            }

            #Query db for Link, making sure current logged in user owns the Link
            link_to_delete = db.session.scalar(
                sa.select(Link).where(Link.id == link_id, Link.user_id == self.id)
            )

            #If Link exists, delete it
            if link_to_delete:
                db.session.delete(link_to_delete)
                db.session.commit()
                return_dictionary["response"] = "Deleted Link"
            else:
                return_dictionary["status"] = "danger"
                return_dictionary["response"] =  "Link not found or you don't have permission to delete it."

            return return_dictionary

        except Exception:
            # Rollback any database staged changes and throw a 500 error
            db.session.rollback()
            abort(500)



#To enforce DB constraints, I am using an Enum to specify allowed values. During input, the value on the Left of the enum should be added to the fields to be able to save it.
#When object is fetched from the db, for enum fields, it returns an enum object. To get Left side, use <enum>.name, and for right side use <enum>.value
#For System Type
class System_Type(enum.Enum):
    development = "DEVELOPMENT"
    qa          = "QA/UAT"
    production  = "PRODUCTION"

#For Deployment Type
class Deployment_Type(enum.Enum):
    saas    = "SAAS"
    on_prem = "ON-PREM"



#The System class, represents each STEP system added by the User
class System(db.Model):
    
    #Mandatory System Details
    id:              orm.Mapped[int]             = orm.mapped_column(primary_key=True)
    system_name:     orm.Mapped[str]             = orm.mapped_column(sa.String(length=15), index=True)
    system_url:      orm.Mapped[str]             = orm.mapped_column(sa.String(length=2048), index=True)
    system_type:     orm.Mapped[System_Type]     = orm.mapped_column(sa.Enum(System_Type, name="system_type_enum", create_constraint=True), index=True)
    deployment_type: orm.Mapped[Deployment_Type] = orm.mapped_column(sa.Enum(Deployment_Type, name="deployment_type_enum", create_constraint=True), index=True)
    
    #Optional System Details
    step_user_id:       orm.Mapped[str] = orm.mapped_column(sa.String(length=40))
    step_user_password: orm.Mapped[str] = orm.mapped_column(sa.String(length=100))
    default_context:    orm.Mapped[str] = orm.mapped_column(sa.String(length=40))
    default_workspace:  orm.Mapped[str] = orm.mapped_column(sa.String(length=40))

    #Bearer Tokens
    bearer_token: orm.Mapped[Optional[dict]] = orm.mapped_column(sa.JSON)

    #Fetched System Details
    details_fetched_date: orm.Mapped[Optional[datetime]] = orm.mapped_column()
    details_json_string:  orm.Mapped[Optional[dict]]     = orm.mapped_column(sa.JSON)

    #Foreign Key
    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey(User.id, ondelete="CASCADE"), index=True)

    #Relationship of Systems and Users
    user: orm.Mapped[User] = orm.relationship(back_populates="systems")

    def __repr__(self):
        return "This is the {} system, at url {}, of type {}.".format(self.system_name, self.system_url, self.system_type)


#The Quick Access Links Class, representing each link added by the user
class Link(db.Model):
    
    #Mandatory Link Details
    id:            orm.Mapped[int]             = orm.mapped_column(primary_key=True)
    link_name:     orm.Mapped[str]             = orm.mapped_column(sa.String(length=30), index=True)
    link_url:      orm.Mapped[str]             = orm.mapped_column(sa.String(length=2048), index=True)
    
    #Foreign Key
    user_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey(User.id, ondelete="CASCADE"), index=True)

    #Relationship of Links and Users
    user: orm.Mapped[User] = orm.relationship(back_populates="links")

    def __repr__(self):
        return "Link is named {} and points to url {}.".format(self.link_name, self.link_url)


#The PageVisit class, for tracking user activity
class PageVisit(db.Model):
    id:           orm.Mapped[int]      = orm.mapped_column(primary_key=True)
    page_name:    orm.Mapped[str]      = orm.mapped_column(sa.String(length=100), index=True)
    visit_count:  orm.Mapped[int]      = orm.mapped_column(default=0)
    last_visited: orm.Mapped[datetime] = orm.mapped_column(default=lambda: datetime.now(timezone.utc))

    #Foreign Key
    user_id:      orm.Mapped[int]      = orm.mapped_column(sa.ForeignKey(User.id, ondelete="CASCADE"), index=True)

    #Relationship of Page Visits and Users
    user: orm.Mapped[User] = orm.relationship(back_populates="page_visits")

    def __repr__(self):
        return "Page {} was visited by user {} {} times.".format(self.page_name, self.user_id, self.visit_count)

    @classmethod
    def record_visit(cls, user_id, page_name):
        try:
            # Check if visit record exists for this user and page
            visit = db.session.scalar(sa.select(cls).where(cls.user_id == user_id).where(cls.page_name == page_name))
            
            if visit:
                visit.visit_count += 1
                visit.last_visited = datetime.now(timezone.utc)
            else:
                visit = cls(user_id=user_id, page_name=page_name, visit_count=1, last_visited=datetime.now(timezone.utc))
                db.session.add(visit)
            db.session.commit()
        except Exception:
            db.session.rollback()