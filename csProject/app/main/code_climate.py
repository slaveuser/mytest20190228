from flask import flash
from .helpers import create_json_file, delete_file#, update_codeclimate_table
from ..models import Code_Climate, Archive
from ..extensions import db
from sqlalchemy import and_
from ..constants import codeclimate_token, slave_username
from .data_dict import file_ext_dict
from datetime import timedelta, date
from collections import defaultdict
import requests, json, humanize

def add_repo(repo_url):
	api_url = 'https://api.codeclimate.com/v1/github/repos'

	headers = {
		'Accept': 'application/vnd.api+json', 
		'Content-Type': 'application/vnd.api+json', 
		'Authorization': 'Token token={}'.format(codeclimate_token)
	}

	filename = create_json_file(repo_url)

	with open(filename, 'rb') as f:
		response = requests.post(api_url, headers=headers, data=f.read())

 	delete_file(filename)

	resp_data = json.loads(response.text or response.content)

	if response.status_code == 201:
		codeclimate_id = resp_data['data']['id']
	else:
		print resp_data['errors'][0]['detail']
		return None
	
	return codeclimate_id

def get_data(repo_id, github_slug, timestamp):
	response = requests.get('https://api.codeclimate.com/v1/repos/'+repo_id)
	data = {}
	
	if response.status_code == 200:
		resp_data = json.loads(response.text or response.content)
		snapshot_id = resp_data['data']['relationships']['latest_default_branch_snapshot']['data']['id']
		badge_token = resp_data['data']['attributes']['badge_token']

		if snapshot_id and badge_token:
			response = requests.get('https://api.codeclimate.com/v1/repos/{}/snapshots/{}'.format(repo_id,snapshot_id))
			resp_data = json.loads(response.text or response.content)
			data['id'] = repo_id
			data['lines_of_code'] = resp_data['data']['attributes']['lines_of_code']
			data['issues_count'] = resp_data['data']['meta']['issues_count']
			data['issues_remediation'] = humanize.naturaltime(timedelta(minutes=resp_data['data']['meta']['measures']['remediation']['value'])).replace(' ago','')
			data['tech_debt_ratio'] = str(resp_data['data']['meta']['measures']['technical_debt_ratio']['value']) + '%'
			data['tech_debt_ratio'] = "%.2f%%" % resp_data['data']['meta']['measures']['technical_debt_ratio']['value']
			data['tech_debt_remediation'] = humanize.naturaltime(timedelta(minutes=resp_data['data']['meta']['measures']['technical_debt_ratio']['meta']['remediation_time']['value'])).replace(' ago','')
			data['tech_debt_implementation'] = humanize.naturaltime(timedelta(minutes=resp_data['data']['meta']['measures']['technical_debt_ratio']['meta']['implementation_time']['value'])).replace(' ago','')
			data['snapshot'] = snapshot_id
			data['badge_token'] = badge_token
			data['github_slug'] = github_slug
			data['timestamp'] = timestamp

			store_cc_data(data)
	
	return data

def get_issues_data(repo_id, snapshot_id, language):
	response = requests.get('https://api.codeclimate.com/v1/repos/{}/snapshots/{}/issues'.format(repo_id, snapshot_id))

	data = defaultdict(list)
	try:
		file_extensions = file_ext_dict[language.lower()]
	except:
		flash('Language not supported', 'danger')
		return data

	if response.status_code == 200:
		resp_data = json.loads(response.text or response.content)

		for issue in resp_data['data']:
			file = issue['attributes']['constant_name']
			fingerprint = issue['attributes']['fingerprint']
			
			if file.endswith(file_extensions):
				issue_data = {
				'fingerprint': issue['attributes']['fingerprint'],
				'category': issue['attributes']['categories'][0],
				'description': issue['attributes']['description'],
				'type' : issue['attributes']['engine_name'],
				'start_line' : issue['attributes']['location']['start_line'],
				'end_line' : issue['attributes']['location']['end_line'],
				'severity' : issue['attributes']['severity']
				}
				data[file].append(issue_data)

	return data

def get_issue_overview(data):
	summary_data = {}
	files_with_issues = len(data.keys())
	summary_data['files_with_issues'] = files_with_issues

	# count issues for each category
	issue_categories = defaultdict(int)
	for file in data:
		for issue in data[file]:
			issue_categories[issue['category'].lower()] += 1

	summary_data['issue_categories'] = issue_categories

	# count types of issues
	issue_types = defaultdict(int)
	for file in data:
		for issue in data[file]:
			issue_types[issue['type'].lower()] += 1

	summary_data['issue_types'] = issue_types

	# count severities
	issue_severities = defaultdict(int)
	for file in data:
		for issue in data[file]:
			issue_severities[issue['severity'].lower()] += 1

	summary_data['issue_severities'] = issue_severities

	return summary_data

def update_codeclimate_table(repo_id, snapshot_id, badge_token):
	print 'updating'
	print repo_id
	print snapshot_id
	print badge_token
	row=db.session.query(Code_Climate).filter(Code_Climate.id == repo_id).first()
	print row
	print row.id
	db.session.query(Code_Climate).filter(Code_Climate.id == repo_id).update({'snapshot': snapshot_id, 'badge_token': badge_token})
	db.session.commit()

def store_cc_data(data):
	exists = db.session.query(Code_Climate).filter(Code_Climate.id == data['id']).first()
	
	if not exists:
		if not data['timestamp']:
			date['timestamp'] = date.today().isoformat()

		# get archive_id for link to archive table
		repo_name = data['github_slug'].replace(slave_username + '/','')[:-8] # cut off owner and last 8 digits (timestamp)
		archive_id = db.session.query(Archive).filter(and_(Archive.name == repo_name, Archive.timestamp == data['timestamp'])).first().id
		data['archive_id'] = archive_id

		code_climate_details = Code_Climate(**data)
		db.session.add(code_climate_details)
		db.session.commit()