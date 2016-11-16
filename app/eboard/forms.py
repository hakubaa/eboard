from flask_wtf import Form
from wtforms import StringField, PasswordField, TextAreaField, \
                    SubmitField, FileField, DateTimeField, SelectField
from wtforms.validators import Required, Email, Length
from app.models import Tag, Project
from app import db

class UploadBookForm(Form):
    title = StringField("Title", validators = [Required()])
    file = FileField("File", validators = [Required()])
    link = StringField("Link")
    author = StringField("Author(s)")
    description = TextAreaField("Description")
    submit = SubmitField("Submit")


class TaskForm(Form):
    title = StringField("Title", validators = [Required()])
    deadline = DateTimeField("Deadline", format='%Y-%m-%d %H:%M', \
        validators = [Required()])
    notes = TextAreaField("Notes")
    submit = SubmitField("Submit")
    tags = StringField("Tags")

        
class NoteForm(Form):
    title = StringField("Title", validators=[Required()])
    body = TextAreaField("What's on your mind?", validators = [Required()])
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
    name = StringField("Name", validators=[Required()])
    description = TextAreaField("Description")
    deadline = DateTimeField("Deadline", format='%Y-%m-%d %H:%M')
    tags = StringField("Tags")
    submit = SubmitField("Submit")    


class MilestoneForm(Form):
    title = StringField("Title", validators=[Required()])
    description = TextAreaField("Description")
    submit = SubmitField("Submit")    