from .monomodule import MonoModule

import requests
import datetime
import re
import urllib.parse

description = '''This module searches github issues.

https://developer.github.com/v3/search/
'''


class CustomModule(MonoModule):
    def set(self):
        self.name = 'github_issue'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = [
            {'name': 'CreatedOrUpdated', 'value': 'created', 'choices':['updated', 'created'], 'alias': 'CP'},
            {'name': 'repository', 'value': '', 'alias': 'R'},
            {'name': 'OnlyPR', 'value': 'False', 'choices':['False', 'True'], 'alias': 'PR'},
        ]
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['hours'] = 6

    def isValidRepository(self, name):
        splited = name.split('/')
        if len(splited) != 2:
            return False
        user = splited[0]
        repo = splited[1]
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$', user):
            return False
        if not re.match(r'^[a-zA-Z0-9\-\_]+$', user):
            return False
        return True

    def search(self):
        word = self.query['query']
        if word == '__EMPTY__':
            word = ''
        else:
            if word.find(' ') > 0:
                word.replace(' ', '\" \"')
            word = '\"' + word + '\"'
        repo = self.getParam('repository')
        if repo != None and repo != '' and self.isValidRepository(repo):
            word += ' repo:' + repo
        search_day = datetime.date.today() - datetime.timedelta(3)
        day_str = search_day.strftime('%Y-%m-%d')
        level = self.getParam('CreatedOrUpdated')
        if level != None and level != '':
            word += ' {which}:>{start_date}'.format(which=level, start_date=day_str)
        else:
            level = 'updated'
        type = self.getParam('OnlyPR')
        if type != None and type != '' and type == 'True':
            word += ' type:pr'
        word = urllib.parse.quote_plus(word)
        url = 'https://api.github.com/search/issues?q={query}&sort={which}&order=desc'.format(query=word, which=level)
        search_in_repo = False
        headers = {'Accept': 'application/vnd.github.v3+json'}
        result = requests.get(url, timeout=10, headers=headers)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            issues = []
            for r in resultdata['items']:
                data = {}
                data['title'] = r['title']
                data['state'] = r['state']
                data['created_at'] = r['created_at']
                data['updated_at'] = r['updated_at']
                data['issue:link'] = r['html_url']
                if 'pull_request' in r.keys():
                    data['pull_request'] = True
                else:
                    data['pull_request'] = False
                issues.append(data)
            self.setResultData(issues, filter='DROP', filter_target=['issue:link', 'title'], exclude_target=['issue:link'])
        else:
            resultdata = result.text
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode), response=resultdata))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found issue/pr about `{}`'.format(self.query['name'])]
            message += [x['issue:link'] for x in result]
        else:
            message = []
        return message
