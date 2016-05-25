from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, validators, FileField, SubmitField
from wtforms.validators import DataRequired
from flask.ext.pagedown.fields import PageDownField

class AddFile(Form):
    file = FileField('Field', validators=[DataRequired()])
    note = PageDownField('Note')
    title = StringField('Title')


class SearchForm(Form):
    field = StringField('Thing')


class SignUpForm(Form):
    email = StringField('Email', validators=[validators.DataRequired()])
    password = PasswordField('Password', 
        [validators.Required(), 
        validators.EqualTo('confirm')])
    username = StringField('Username', validators=[validators.DataRequired()])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Sign In')


class SignInForm(Form):
    email = StringField('Email', validators=[
            validators.DataRequired()])
    password = PasswordField('Password')
    submit = SubmitField('Sign In')