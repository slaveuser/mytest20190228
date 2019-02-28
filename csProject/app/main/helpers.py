import sys, json, os, requests, re, time, stat
from flask import current_app as app, abort
from flask_login import current_user
from ..models import OAuth, Code_Climate, Repository, Archive
from ..extensions import db
from sqlalchemy import and_
from dateutil.relativedelta import relativedelta
from datetime import date
from ..constants import github_api_url_base

def get_user_token():
	for u in db.session.query(OAuth).all():
		if u.user_id == current_user.id:
			return u.token['access_token']
	return None

def formatRepoStats(repo_stats):
	for repo,stat in repo_stats.items():
		del stat['description']
		del stat['owner']
	
	return repo_stats

def chartFormatRepoStats(repo_stats):
	formatted = ['Statistic']
	for repo, stats in repo_stats.iteritems():
		formatted.append(repo)
	ChartFormatted = [formatted]

	# stats = ['stargazers', 'watchers', 'subscribers', 'size (KB)', 'open issues', 'forks']
	stats = ['stargazers', 'subscribers',  'open issues', 'forks']
	for s in stats:
		stat = [s]
		for repo, values in repo_stats.iteritems():
			for k,v in values.iteritems():
				if k == s:
					stat.append(v)
		ChartFormatted.append(stat)
		
	return ChartFormatted

# def store_repo_info(url, **kwargs):
# 	_url = url.replace('.git','')
# 	if not ('path' in kwargs):
# 		path = generate_download_path(url)
# 	else:
# 		path = kwargs['path']

# 	download_folder = path.replace(os.path.dirname(os.getcwd()),'')

# 	api_url = _url.replace('https://github.com/', github_api_url_base + 'repos/')
# 	api_url = api_url.replace('http://github.com/', github_api_url_base + 'repos/') # in case of http instead of https
# 	headers = {'Authorization': 'token %s' % get_user_token()}

# 	response = requests.get(api_url, headers=headers)

# 	if response.status_code == 200:
# 		repo_info = json.loads(response.text or response.content)
# 		name = repo_info['name']
# 		owner = repo_info['owner']['login']
# 		slug = repo_info['full_name']

# 		exists = db.session.query(Repository).filter_by(github_slug=slug).first()
# 		if not exists:
# 			repo = Repository(url=url, name=name, owner=owner, github_slug=slug, download_folder=download_folder)
# 			db.session.add(repo)
# 			db.session.commit()

def store_archive_info(url, time_series, archive_folder):
	slug = re.sub(r"http(s)?://github\.com/",'', url).replace('.git','').strip()
	owner, name = slug.split('/')
	time_intervals = get_time_intervals(time_series)
	relative_folder = os.path.join(*archive_folder.rsplit(os.path.sep, 3)[-3:])

	for timestamp in time_intervals:
		_relative_folder = os.path.join(relative_folder, str(timestamp))

		exists = db.session.query(Archive).filter_by(archive_folder=archive_folder).first()
		if not exists:
			archive = Archive(url=url, name=name, owner=owner, github_slug=slug, timestamp=str(timestamp), archive_folder=_relative_folder)
			db.session.add(archive)
			db.session.commit()

# def generate_download_path(url):
# 	repo_name = os.path.basename(os.path.normpath(url)).strip().replace('_','-')
# 	owner = url.rsplit('/', 2)[-2]
# 	path = os.path.join(os.path.dirname(os.getcwd()), 'repos', owner + '_' + repo_name.replace('.git','').strip())

# 	return path

def create_archive(url):
	repo_name = os.path.basename(os.path.normpath(url)).strip().replace('_','-')
	owner = url.rsplit('/', 2)[-2]
	cwd = os.path.dirname(os.getcwd())
	timestamp = str(int(time.time()))
	# path = '{0}/archive/{1}_{2}/{3}'.format(cwd, owner, repo_name.replace('.git','').strip(), timestamp)
	path = os.path.join(cwd, 'archive', owner + '_' + repo_name.replace('.git','').strip(), timestamp)

	if not os.path.exists(path):
		os.makedirs(path)
    
	return path

def generate_github_slug(repository):
	owner = repository.split('_')[0].replace('_','/').replace('-','_')
	repo_name = repository.split('_')[1].replace('_','/').replace('-','_')
	slug = owner + '/' + repo_name

	return slug

def generate_repo_dir(repository, **kwargs):
	try:
		if kwargs['timestamp'] is not None:
			path = db.session.query(Archive).filter(and_(Archive.archive_folder.like('%'+repository+'%'), Archive.timestamp==kwargs['timestamp'])).first().archive_folder
		else:
			path = db.session.query(Repository).filter(Repository.download_folder.like('%'+repository)).first().download_folder
	except Exception as ex:
		print ex
		print 'Repository not found in database'
		return# abort(404)

	repo_dir = os.path.join(os.path.dirname(os.getcwd()), path)
	return repo_dir

def generate_github_api_url(repository, **kwargs):
	try:
		if kwargs['timestamp'] is not None:
			slug = db.session.query(Archive).filter(and_(Archive.archive_folder.like('%'+repository+'%'), Archive.timestamp==kwargs['timestamp'])).first().github_slug
		else:
			slug = db.session.query(Repository).filter(Repository.download_folder.like('%'+repository)).first().github_slug
	except Exception as ex:
		print ex
		print 'Repository not found in database'
		return# abort(404)


	api_url = '{}repos/{}'.format(github_api_url_base, slug.lower())

	return api_url

def get_repo_language(repository, **kwargs):
	api_url = generate_github_api_url(repository, timestamp=kwargs['timestamp'])
	
	if not api_url:
		return
	
	headers = {'Authorization': 'token %s' % get_user_token()}
	response = requests.get(api_url, headers=headers)

	if response.status_code == 200:
		data = json.loads(response.text or response.content)
		return data['language']
	else:
		return

def create_json_file(url):
	data = {
		"data": {
			"type": "repos",
			"attributes": {
				"url": "" + url + ""
			}
		}
	}

	with open('code_climate_add_repo.json', 'w') as outfile:
		json.dump(data, outfile)

	return 'code_climate_add_repo.json'

def delete_file(path):
	if os.path.exists(path):
		os.remove(path)

# def update_codeclimate_table(repo_id, snapshot_id, badge_token):
# 	db.session.query(Code_Climate).filter(Code_Climate.id == repo_id).update({'latest_snapshot': snapshot_id, 'badge_token': badge_token})
# 	db.session.commit()

def get_time_intervals(time_series):
	intervals = []
	today = date.today()

	# 1, 3, 6 or 12
	if time_series == 1:
		for i in (0, 7, 14, 21, 28):
			intervals.append(today + relativedelta(days=-i))
	elif time_series == 3:
		for i in (0, 1, 2, 3):
			intervals.append(today + relativedelta(months=-i))
	elif time_series == 6:
		for i in (0, 2, 4, 6):
			intervals.append(today + relativedelta(months=-i))
	elif time_series == 12:
		for i in (0, 4, 8, 12):
			intervals.append(today + relativedelta(months=-i))

	return intervals

def get_sha(github_slug, timestamp, user_token):
	headers = {'Authorization': 'token %s' % user_token}
	api_url = '{}repos/{}/commits?until={}Z'.format(github_api_url_base, github_slug, timestamp.isoformat())

	response = requests.get(api_url, headers=headers)
	resp_data = json.loads(response.text or response.content)

	if response.status_code == 200:
		try:
			return resp_data[0]['sha']
		except:
			return
	else:
		print resp_data['message']


def walklevel(some_dir, level):
	low_level_dirs = []
	some_dir = some_dir.rstrip(os.path.sep)
	assert os.path.isdir(some_dir)
	num_sep = some_dir.count(os.path.sep)
	for root, dirs, files in os.walk(some_dir):
		num_sep_this = root.count(os.path.sep)
		if num_sep + level <= num_sep_this:
			yield root
			del dirs[:]
