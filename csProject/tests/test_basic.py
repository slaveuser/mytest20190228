import unittest
from base import BaseTestCase
from flask import current_app as app
from urlparse import urlparse
from testdata import TestUser

class FlaskTestCase(BaseTestCase):

	# Ensure that unauthorized request returns unauthorized error and 401 page loads
	def test_index_unauthorized(self):
		self.app.config['LOGIN_DISABLED'] = False
		self.app.login_manager.init_app(app)
		response = self.client.get('/', content_type='html/text')
		self.assertEqual(response.status_code, 401)
		self.assertIn(b'You must be logged in', response.data)

	# Ensure that unauthorized user is redirected to GitHub to login
	def test_redirect_github_login(self):
		self.app.config['LOGIN_DISABLED'] = False
		self.app.login_manager.init_app(app)
		response = self.client.get('/login', follow_redirects=False)
		expectedPath = '/login/github'
		self.assertEqual(response.status_code, 302)
		self.assertEqual(urlparse(response.location).path, expectedPath)

	""" Log in with existing user - github handles login so bypass 
	'@login_required' decorator and ensure that index page loads with 200 status
	"""
	def test_login_authorized(self):
		response = self.client.get('/', follow_redirects=False)
		self.assertIn(b'Welcome', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that user can logout and logout page loads
	def test_logout(self):
		response = self.client.get('/logout', content_type='html/text')
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'You have been logged out', response.data)

	# Ensure that statistics page loads
	def test_stats_page(self):
		response = self.client.get('/stats', content_type='html/text')
		self.assertIn(b'Statistics', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that repositories page loads
	def test_repositories_page(self):
		# response = self.client.get('/repositories', content_type='html/text')
		# self.assertIn(b'Repositories', response.data)
		# self.assertEqual(response.status_code, 200)

	# Ensure that browse page loads
	def test_browse_page(self):
		response = self.client.get('/browse', content_type='html/text')
		self.assertIn(b'Browse', response.data)
		self.assertEqual(response.status_code, 200)

	# Ensure that downloads page loads
	# def test_downloads_page(self):
	# 	response = self.client.get('/downloads', content_type='html/text')
	# 	self.assertIn(b'Downloads', response.data)
	# 	self.assertEqual(response.status_code, 200)

	# # Ensure that analysis page loads
	# def test_analysis_page(self):
	# 	response = self.client.get('/analyse', content_type='html/text')
	# 	self.assertIn(b'Code Quality Analysis', response.data)
	# 	self.assertEqual(response.status_code, 200)

	# # Ensure that quality issues page loads
	# def test_quality_issues_page(self):
	# 	response = self.client.get('/quality_issues', content_type='html/text')
	# 	self.assertIn(b'Code Quality Issues', response.data)
	# 	self.assertEqual(response.status_code, 200)

	# Ensure that archive page loads
	# def test_archive_page(self):
	# 	response = self.client.get('/archive', content_type='html/text')
	# 	self.assertIn(b'Archive', response.data)
	# 	self.assertEqual(response.status_code, 200)

			
if __name__ == '__main__':
	unittest.main()