from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, validators, FileField
from wtforms.validators import DataRequired

class AddFile(Form):
	file = FileField('Field', validators=[DataRequired()])
	note = StringField('Note')
	title = StringField('Title')

class SearchForm(Form):
	field = StringField('Thing')