from flask_wtf import Form
from wtforms import StringField, PasswordField, TextAreaField, \
                    SubmitField, FileField, DateTimeField, SelectField
from wtforms.validators import DataRequired, Email, Length
from app.models import Tag, Project
from app import db

class UploadBookForm(Form):
    title = StringField("Title", validators = [DataRequired()])
    file = FileField("File", validators = [DataRequired()])
    link = StringField("Link")
    author = StringField("Author(s)")
    description = TextAreaField("Description")
    submit = SubmitField("Submit")


class TaskForm(Form):
    title = StringField("Title", validators = [DataRequired()])
    deadline = DateTimeField("Deadline", format='%Y-%m-%d %H:%M', \
        validators = [DataRequired()])
    body = TextAreaField("Body")
    submit = SubmitField("Submit")
    tags = StringField("Tags")


class NoteForm(Form):
    title = StringField("Title", validators=[DataRequired()])
    body = TextAreaField("What's on your mind?", validators = [DataRequired()])
    tags = StringField("Tags")
    submit = SubmitField("Submit")

class NoteFilterForm(Form):
    tag = SelectField("Tag", choices = [])
    project = SelectField("Project", choices=[])

    def __init__(self, tags = None, projects = None):
        super(NoteFilterForm, self).__init__()

        self.tag.choices = [ ("all", "-- All --")] +\
            [ (str(tag.id), tag.name) for tag in tags ]
        self.project.choices = [ ("all", "-- All Projects --"),
            ("unbound", "-- Unbound Notes --")] +\
            [ (str(project.id), project.name) for project in projects ]

class ProjectForm(Form):
    name = StringField("Name", validators=[DataRequired()])
    desc = TextAreaField("Description")
    deadline = DateTimeField("Deadline", format='%Y-%m-%d %H:%M',
                             validators=[DataRequired()])
    # tags = StringField("Tags")
    submit = SubmitField("Submit")    


class MilestoneForm(Form):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description")
    submit = SubmitField("Submit")    