from .extensions import db
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin
from flask_login import UserMixin
# from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
	username = db.Column(db.String(45), unique=True)

	def __repr__(self):
		return '<user %r>' % self.username

class OAuth(OAuthConsumerMixin, db.Model):
	user_id = db.Column(db.Integer, db.ForeignKey(User.id))
	user = db.relationship(User)

class Code_Climate(db.Model):
	id = db.Column(db.String(80), primary_key=True, unique=True)
	# archive_id = db.Column(db.Integer, unique=True, db.ForeignKey('archive.archive_id'))
	archive_id = db.Column(db.Integer, db.ForeignKey('archive.id'))
	github_slug = db.Column(db.String(150))
	timestamp = db.Column(db.String(10))
	snapshot = db.Column(db.String(150))
	badge_token = db.Column(db.String(150))
	lines_of_code = db.Column(db.Integer)
	issues_count = db.Column(db.Integer)
	issues_remediation = db.Column(db.String(50))
	tech_debt_ratio = db.Column(db.String(10))
	tech_debt_implementation = db.Column(db.String(50))
	tech_debt_remediation = db.Column(db.String(50))

	# archive = relationship("Archive", uselist=False, back_populates="code_climate")
	archive = db.relationship('Archive')

class Repository(db.Model):
	url = db.Column(db.String(150), primary_key=True, unique=True)
	owner = db.Column(db.String(150))
	name = db.Column(db.String(150))
	github_slug = db.Column(db.String(150), unique=True)
	download_folder = db.Column(db.String(150))

class Archive(db.Model):
	id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
	url = db.Column(db.String(150))
	owner = db.Column(db.String(150))
	name = db.Column(db.String(150))
	github_slug = db.Column(db.String(150))
	timestamp = db.Column(db.String(10))
	archive_folder = db.Column(db.String(150))

	# code_climate = relationship("Code_Climate", back_populates="archive")
	code_climate = db.relationship("Code_Climate", backref="origin", uselist=False)
	