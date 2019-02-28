from flask_wtf import FlaskForm
from wtforms import StringField, RadioField
from wtforms.validators import InputRequired

class RepoURLForm(FlaskForm):
	url = StringField('url', validators=[InputRequired()])
	view = StringField('view', default='raw')

class RepoURLArchiveForm(FlaskForm):
	url = StringField('url', validators=[InputRequired()])
	time_series = RadioField('time_series', choices=[('1','1 Month'),('3','3 Months'),('6','6 Months'),('12','12 Months')], validators=[InputRequired()])
