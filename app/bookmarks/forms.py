from flask_wtf import Form
from wtforms import (
    StringField, PasswordField, TextAreaField, 
    SubmitField, FileField, DateTimeField, SelectField, IntegerField
)
from wtforms.validators import DataRequired


class BookmarkForm(Form):
    title = StringField("Title", validators=[DataRequired()])
    submit = SubmitField("Submit")