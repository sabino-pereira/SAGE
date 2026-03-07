from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app import db
from app.models import User
import sqlalchemy as sa


#User Registration Form
class RegistrationForm(FlaskForm):
    username        = StringField("Username", render_kw={"autofocus": True}, validators=[DataRequired(), Length(min=3, max=10, message="Username should be between %(min)d to %(max)d characters.")])
    email           = StringField("Email", validators=[DataRequired(), Email()])
    password        = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=100, message="Password should be minimum %(min)d characters long.")])
    repeat_password = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo("password", message="Passwords don't match.")])
    submit          = SubmitField("Register")

    #Throw error if username is already taken or there is a space in the username
    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError("Username not available!")
        elif ' ' in username.data:
            raise ValidationError("No spaces allowed in username.")
    
    #Throw error is email is already taken
    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError("Email already in use, try a different one!")


#User Login Form
class LoginForm(FlaskForm):
    username    = StringField("Username or Email", render_kw={"autofocus": True}, validators=[DataRequired(), Length(max=254)])
    password    = PasswordField("Password", validators=[DataRequired(), Length(max=100)])
    remember_me = BooleanField("Remember Me")
    submit      = SubmitField("Sign In")