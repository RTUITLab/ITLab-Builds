from flask import Flask, send_file
from github import Github
import json
import re
import requests
from flask import request
from decouple import config

GITHUB_API_KEY=config('GH_KEY')

if not GITHUB_API_KEY:
    print('No GITHUB API KEY')
    exit()

AUTHORIZATION_HEADER='token %s' % GITHUB_API_KEY
g = Github(GITHUB_API_KEY)
org = g.get_organization("RTUITLab")
app = Flask(__name__)


@app.route('/api/builds/repos/')
def get_repos():
    answer = []
    for repo in org.get_repos():
        answer.append({'name': repo.name, 'description': repo.description, 'lastPushTime': str(repo.pushed_at),
                       "isArchived": repo.archived})
    return json.dumps(answer)


@app.route('/api/builds/repos/<repoName>/releases')
def get_releases_list(repoName):
    answer = []
    repo = org.get_repo(repoName)
    reg_exp = re.compile(r'.*\/([^\/]*)$')
    for i in repo.get_releases():
        assets = []
        for k in i.raw_data['assets']:
            assets.append((reg_exp.match(k['browser_download_url'])[1]))
        assets.append('zip')
        assets.append('tar')
        answer.append({'id': i.id, 'tagName': i.tag_name, 'assets': assets})
    return json.dumps(answer)


@app.route('/api/builds/repos/<repoName>/releases/<releaseId>/<filename>')
def download_release_asset(repoName, releaseId, filename):
    release = org.get_repo(repoName).get_release(releaseId)
    headers = {'Authorization': AUTHORIZATION_HEADER}
    reg_exp = re.compile(r'.*\/([^\/]*)$')
    i = org.get_repo(repoName).get_release(releaseId)
    assets = []
    for k in i.raw_data['assets']:
        assets.append(({'name': reg_exp.match(k['browser_download_url'])[1], 'id': k['id']}))
    assets.append(i.zipball_url)
    assets.append(i.tarball_url)
    if filename == 'zip':
        r = requests.get(assets[-2], headers=headers)
        print(assets[-2])
        target = repoName + '_release=' + str(releaseId) + '_zipball.zip'
    elif filename == 'tar':
        r = requests.get(assets[-1], headers=headers)
        print(assets[-1])
        target = repoName + '_release=' + str(releaseId) + '_tarball.tar.gz'
    else:
        for k in range(len(assets) - 2):
            if filename == (assets[k]['name']):
                target = filename
                headers = {'Accept': 'application/octet-stream',
                           'Authorization': AUTHORIZATION_HEADER}
                r = requests.get(
                    'https://api.github.com/repos/RTUITLab/' + repoName + '/releases/assets/' + str(assets[k]['id']),
                    headers=headers)
    with open(target, 'wb') as the_file:
        the_file.write(r.content)
    return send_file(target, as_attachment=True)



if __name__ == '__main__':
    app.run()   