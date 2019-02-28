from flask import Blueprint, render_template, request, flash, current_app, g, jsonify, url_for, redirect
from flask_login import login_required, current_user
from rq import push_connection, pop_connection, Queue
from rq.registry import StartedJobRegistry
from .. import tasks
from .helpers import (get_user_token, chartFormatRepoStats, formatRepoStats, get_repo_language, 
	generate_repo_dir, create_archive, store_archive_info, walklevel)
from .forms import RepoURLForm, RepoURLArchiveForm
from . import analysis_functions
from . import code_climate
from github import Github
from sqlalchemy import and_
from ..constants import github_api_url_base, github_headers, slave_username
from ..extensions import db
from ..models import Repository, Code_Climate, Archive
import redis
import pygit2
import requests, json, urllib, os, time, re

bp = Blueprint('main', __name__)

def get_redis_connection():
	redis_connection = getattr(g, '_redis_connection', None)
	if redis_connection is None:
		redis_url = current_app.config['REDIS_URL']
		redis_connection = g._redis_connection = redis.from_url(redis_url)
	return redis_connection

def get_current_rq_jobs():
	registry = StartedJobRegistry('default', connection=get_redis_connection())
	running_job_ids = registry.get_job_ids() 
	return len(running_job_ids)

@bp.before_request
def push_rq_connection():
	push_connection(get_redis_connection())

@bp.teardown_request
def pop_rq_connection(exception=None):
	pop_connection()

@bp.route('/status/<job_id>')
def job_status(job_id):
	q = Queue()
	job = q.fetch_job(job_id)
	if job is None:
		response = {'status': 'unknown'}
	else:
		response = {
			'status': job.get_status(),
			'result': job.result,
		}
		if job.is_failed:
			response['message'] = job.exc_info.strip().split('\n')[-1]
	return jsonify(response)

@bp.route('/run_archive_task', methods=['POST'])
def run_archive_task():
	form = RepoURLArchiveForm(request.form)

	if form.validate():
		url = request.form.get('url')

		time_series = int(request.form['time_series'])
		archive_folder = create_archive(url)
		store_archive_info(url, time_series, archive_folder)

		token = get_user_token()
		try:
			github_slug = db.session.query(Archive).filter_by(url=url).first().github_slug
		except:
			return jsonify('Job failed. Contact administrator.'), 400

		q = Queue()
		job = q.enqueue(tasks.archive_repository, archive_folder, url, github_slug, time_series, token, timeout=6000)
		return jsonify({}), 202, {'Location': url_for('main.job_status', job_id=job.get_id())}
	else:
		return jsonify('Please fill out all fields.'), 400

# @bp.route('/test', methods=['GET'])
# @login_required
# def test():
# 	from google.cloud import bigquery

# 	client = bigquery.Client()

# 	# Perform a query.
# 		# 'SELECT name FROM `bigquery-public-data.usa_names.usa_1910_2013` '
# 	QUERY = (
# 		'SELECT * FROM `[githubarchive:day.20150101]` '
# 		'LIMIT 100')
# 	# QUERY = ("SELECT event as issue_status, COUNT(*) as cnt FROM (SELECT type, repo.name, actor.login, JSON_EXTRACT(payload, '$.action') as event FROM (TABLE_DATE_RANGE([githubarchive:day.], TIMESTAMP('2015-01-01'), TIMESTAMP('2015-02-01'))) WHERE type = 'IssuesEvent')gROUP by issue_status;")
# 	query_job = client.query(QUERY)  # API request
# 	rows = query_job.result()  # Waits for query to finish

# 	for row in rows:
# 		print(row.name)

# 	return 'done'


@bp.route('/test', methods=['GET'])
@login_required
def test():
	repo_dir = '/mnt/c/users/gmcpo/Documents/dev/CSC3002-Project/archive/GaryMcPolin_ChurchillMouldingsLtd/1550664521/2018-11-20'
	token=get_user_token()
	g = Github(token)
	repo = g.get_repo("GaryMcPolin/ChurchillMouldingsLtd")
	print repo.language
	# repository_path = pygit2.discover_repository(repo_dir)
	# repo = pygit2.Repository(repository_path)
	# print repo.describe
	return 'abc'

@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
	form = RepoURLArchiveForm()

	archive_directory = os.path.join(os.path.dirname(os.getcwd()),'archive')
	archived_repos = {}

	for repo in walklevel(archive_directory, 3):
		name = repo.split(os.path.sep)[-3]
		timestamp = repo.split(os.path.sep)[-1]
		
		if not name in archived_repos:
			archived_repos[name] = set()

		archived_repos[name].add(timestamp)

	return render_template('archive.html', form=form, archived_repos=archived_repos)

@bp.route('/stats', methods=['GET', 'POST'])
@login_required
def stats():
	form = RepoURLForm()

	if form.validate_on_submit():
		urls = request.form.to_dict(flat=False)
		urlList = urls.itervalues().next()

		token = get_user_token()

		if not token:
			return 'Unauthorised'
	
		g = Github(token)
		repo_stats={}

		for r in urlList:
			repo_name='/'.join(r.rsplit('/', 2)[1:]).replace('.git','').replace(" ", "")
			try:
				repo = g.get_repo(repo_name)
				repo_stats[repo.name] = {}
				repo_stats[repo.name]['stargazers'] = repo.stargazers_count
				repo_stats[repo.name]['watchers'] = repo.watchers
				repo_stats[repo.name]['subscribers'] = repo.subscribers_count
				repo_stats[repo.name]['size (KB)'] = repo.size
				repo_stats[repo.name]['owner'] = repo.owner.login
				repo_stats[repo.name]['open issues'] = repo.open_issues_count
				repo_stats[repo.name]['forks'] = repo.forks_count
				repo_stats[repo.name]['description'] = repo.description
				repo_stats[repo.name]['branches'] = repo.get_branches().totalCount
			except:
				flash("Failed to extract statistics for repository '{}' ({})".format(repo_name.capitalize(), r), 'danger')

		chart_stats = chartFormatRepoStats(repo_stats)
		repo_stats = formatRepoStats(repo_stats)

		return render_template('stats.html', form=form, stats=repo_stats, chart_stats=chart_stats)

	return render_template('stats.html', form=form)

@bp.route('/repositories')
@login_required
def repositories():
	repositories={}

	api_url = '{}users/{}/repos'.format(github_api_url_base, current_user.username)
	headers = {'Authorization': 'token %s' % get_user_token()}
	response = requests.get(api_url, headers=headers)

	if response.status_code == 200:
		repository_data = json.loads(response.text or response.content)

		for r in repository_data:
			repositories[r['name']]= r['html_url']
	else:
		return render_template(str(response.status_code)+'.html')

	return render_template('repositories.html', repositories=repositories)

@bp.route('/browse', methods=['GET', 'POST'])
@login_required
def browse():
	url = 'https://github-trending-api.now.sh/repositories'

	language = request.args.get('language')
	since = request.args.get('since')

	if language:
		url += '?language='+urllib.quote(language.encode("utf-8"))

		if since:
			url += '&since='+since
	elif since:
			url += '?since='+since

	response = requests.get(url, headers=github_headers)
	data = response.text.encode("utf-8")
	json_data = json.loads(data)

	trending_repos = {}

	for repo in json_data:
		try:
			name = repo['name']
			trending_repos[name] = {}
			trending_repos[name]['description'] = repo['description']
			trending_repos[name]['url'] = repo['url']
			trending_repos[name]['language'] = repo['language']
		except KeyError:
			pass

	return render_template('browse.html', trending_repos=trending_repos)

@bp.route('/downloads')
@login_required
def downloads():
	downloads_dir = os.path.join(os.path.dirname(os.getcwd()), 'repos')

	repositories = []

	for repo in os.listdir(downloads_dir):
		repositories.append(repo)

	return render_template('downloads.html', repos=repositories)

@bp.route('/analyse', methods=['GET', 'POST'])
@login_required
def analyse():
	repository = request.args.get('repo')
	timestamp = request.args.get('timestamp')

	if not repository:
		return redirect(url_for('main.downloads'))

	language = get_repo_language(repository, timestamp=timestamp)

	if not language:
		flash('Project could not be found on GitHub.', 'danger')
		return redirect(url_for('main.analyse'))

	repo_dir = generate_repo_dir(repository, timestamp=timestamp)

	if not repo_dir:
		flash('Project could not be found on GitHub.', 'danger')
		return redirect(url_for('main.analyse'))

	all_data = {}
	all_data['code_size_data'] = analysis_functions.countLinesOfCode(language, repo_dir)
	# all_data['functions_data'] = analysis_functions.countFunctions(language, repo_dir)
	all_data['classes_data'] = analysis_functions.countClasses(language, repo_dir)
	# return jsonify(all_data)

	try:
		archived = db.session.query(Archive).filter(and_(Archive.archive_folder.like('%'+repository+'%'), \
			Archive.timestamp==timestamp)).first().name
	except:
		try:
			github_slug = db.session.query(Repository).filter(and_(Repository.download_folder.like('%'+repository), \
				Repository.owner==current_user.username)).first().github_slug
		except:
			flash('You must archive this repository before analysis', 'danger')
			return redirect(url_for('main.index'))
	else:
		github_slug = slave_username + '/' + repository + timestamp.replace('-','')

	try:
		cc_id = Code_Climate.query.filter_by(github_slug=github_slug).first().id
	except:
		cc_id = code_climate.add_repo("https://github.com/"+github_slug)

		if cc_id:
			time.sleep(45) # allow code climate some time to perform analysis
		else:
			flash('Error: Could not obtain code climate data. Permissions may be required.', 'danger')
			return render_template('results.html', data=all_data)

	cc_data = code_climate.get_data(cc_id, github_slug, timestamp)
	all_data['cc_data'] = cc_data
	
	if request.method == 'POST':
		return jsonify(cc_data)
	else:
		return render_template('results.html', data=all_data)

@bp.route('/quality_issues')
@login_required
def quality_issues():
	id = request.args.get('id')
	# repository = request.args.get('repo')
	timestamp = request.args.get('timestamp')

	github_slug = db.session.query(Code_Climate).filter_by(id=id).first().github_slug


	repository = db.session.query(Archive).filter(Archive.id == Code_Climate.archive_id).\
											filter(Code_Climate.id == id).first().name
	language = get_repo_language(repository, timestamp=timestamp)

	try:
		snapshot_id = Code_Climate.query.filter_by(id=id).first().snapshot
		badge_token = Code_Climate.query.filter_by(id=id).first().badge_token
	except:
		snapshot_id = badge_token = None

	data = code_climate.get_issues_data(id, snapshot_id, language)

	cc_data = {'github_slug': github_slug, 'badge_token': badge_token}
	summary_data = code_climate.get_issue_overview(data)

	return render_template('quality_issues.html', issue_data=data, summary_data=summary_data, cc_data=cc_data)

@bp.route('/analyse_all/<repo_name>', methods=['GET'])
@login_required
def analyse_all(repo_name):
	repos = db.session.query(Archive).filter(Archive.name == repo_name).all()

	if not repos:
		flash('You must archive this repository before analysis', 'danger')
		return redirect(url_for('main.index'))

	headers = {'Cookie': 'session=' + request.cookies['session']}
	data = []

	for repo in repos:
		url = 'http://127.0.0.1:5000/analyse?repo=' + repo.name + '&timestamp=' + repo.timestamp
		response = requests.post(url, headers=headers)
		cc_data = json.loads(response.content)
		if not cc_data:
			flash('An error occurred', 'danger')
			break
		data.append(cc_data)

	# return jsonify(data)
	return render_template('compare.html', repo_name=repo_name, data=data)