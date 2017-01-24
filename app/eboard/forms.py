from flask_wtf import Form
from wtforms import (
    StringField, PasswordField, TextAreaField, 
    SubmitField, FileField, DateTimeField, SelectField, IntegerField
)
from wtforms.validators import DataRequired, Email, Length

from app.models import Tag, Project
from app import db
from app.models import dtformat_default



class TaskForm(Form):
    title = StringField("Title", validators = [DataRequired()])
    deadline = DateTimeField("Deadline", format=dtformat_default, \
        validators = [DataRequired()])
    body = TextAreaField("Body")
    responsible = StringField("Responsible")
    submit = SubmitField("Submit")
    tags = StringField("Tags")


class NoteForm(Form):
    title = StringField("Title", validators=[DataRequired()])
    body = TextAreaField("What's on your mind?", validators = [DataRequired()])
    tags = StringField("Tags")
    submit = SubmitField("Submit")


class ProjectForm(Form):
    name = StringField("Name", validators=[DataRequired()])
    desc = TextAreaField("Description")
    deadline = DateTimeField("Deadline", format=dtformat_default,
                             validators=[DataRequired()])
    submit = SubmitField("Submit")    


class MilestoneForm(Form):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description")
    submit = SubmitField("Submit")    