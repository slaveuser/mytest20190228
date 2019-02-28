from app.models import User
from flask_login import login_user
from base import db

class TestUser():

	def __init__(self):
		self.username = 'GaryMcPolin'
		self.github_token = {"access_token": "763f5bfe1e43f05c59525f40973477fb212c2a95", "token_type": "bearer", "scope": [""]}
		self.user = User(username=self.username)
		db.session.add(self.user)
		db.session.commit()

	def get_user(self):
		return self.user

	def get_token(self):
		return self.github_token['access_token']

