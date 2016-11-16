from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Email, Length

class SignInForm(Form):
    username = StringField("Username", validators = [Required()])
    password = PasswordField("Password", validators = [Required()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Submit")