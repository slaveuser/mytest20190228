from main.helpers import create_archive, get_time_intervals, get_sha, get_user_token
from constants import github_api_url_base, slave_token as s_token
import pygit2
import git
import requests, os, shutil, json

def archive_repository(archive_path, url, github_slug, time_series, token):
	''' Download previous versions of the chosen repository at the specified
	intervals and commit these to slave account for future analysis '''
	# archive_path = create_archive(url)
	time_intervals = get_time_intervals(time_series)

	for timestamp in time_intervals:
		sha = get_sha(github_slug, timestamp, token)

		if sha:
			oid = pygit2.Oid(hex=sha)
			download_path = os.path.join(archive_path, str(timestamp))

			try:
				repo = pygit2.clone_repository(url, download_path, bare=False)
				init_repo(oid, download_path)
				u_name = github_slug.split('/')[1] + str(timestamp).replace('-','')
				bare_url = create_bare_repo(u_name)
				if bare_url:
					commit_files(bare_url, download_path)
			except Exception as ex:
				return str(type(ex).__name__)
				# return '{}: {}'.format(type(ex).__name__, ex.args[0])
				# os.system('rmdir /S /Q "{}"'.format(archive_path))
		else:
			return 'Error: Could not access commit history for given time period'.format(url)
			# os.system('rmdir /S /Q "{}"'.format(archive_path))
	return 'Successfully archived {}'.format(url)

def init_repo(oid, download_path):
	''' Revert repo to the state it was in at the specified timestamp (oid) and 
	remove connection to src repository before committing for analysis '''
	repo = pygit2.init_repository(download_path, bare=False)
	repo.reset(oid, pygit2.GIT_RESET_HARD)
	shutil.rmtree(os.path.join(download_path, '.git'))

def create_bare_repo(repo_name):
	''' Create empty repository with descriptive name on slave github account.
	Returns url of new repostiory or None if unsuccessful '''
	api_url = '{}user/repos'.format(github_api_url_base)
	headers = {'Authorization': 'token %s' % s_token}
	data = {"name": repo_name, "private": False}
	response = requests.post(api_url, headers=headers, json=data)

	if response.status_code == 201:
		print 'Created new repository {}'.format(repo_name)
		return json.loads(response.text or response.content)['ssh_url']
	else:
		print response.text

def commit_files(bare_url, download_path):
	''' Commit and push files to repository on slave account for future analysis '''
	file_list = []
	for (dirpath, dirnames, filenames) in os.walk(download_path):
		if '.git' not in dirpath:
			file_list += [os.path.join(dirpath, file) for file in filenames]
	
	try:
		repo = git.Repo.init(download_path)
		repo.index.add(file_list)
		repo.index.commit(message='Initial commit')
		repo.git.push(bare_url, 'HEAD:master')
	except:
		print 'Failed to commit to {}'.format(bare_url)
	print 'Committed successfully to {}'.format(bare_url)