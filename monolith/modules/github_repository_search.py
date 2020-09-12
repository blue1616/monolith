from .monomodule import MonoModule

import requests
import datetime
import urllib.parse

description = '''This module searches github repository.
Set search keyword as a Query.

https://developer.github.com/v3/search/#search-repositories
'''


class CustomModule(MonoModule):
    def set(self):
        self.name = 'github'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = [
            {'name': 'CreatedOrPushed', 'value': 'created', 'choices':['created','pushed'], 'alias': 'CP'},
            {'name': 'SearchIn', 'value': 'name,description', 'choices':['name,description','name,description,readme'], 'alias': 'IN'},
        ]
        self.default_query['expire_date'] = 180
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['hours'] = 6

    def search(self):
        word = self.query['query']
        search_day = datetime.date.today() - datetime.timedelta(3)
        day_str = search_day.strftime('%Y-%m-%d')
        createdOrPushed = self.getParam('CreatedOrPushed')
        if createdOrPushed == None:
            createdOrPushed = 'created'
        searchIn = self.getParam('SearchIn')
        if searchIn == None:
            searchIn = 'in:name,description'
        else:
            searchIn = 'in:' + searchIn
        github_url = 'https://api.github.com/search/repositories?q='
        if word.find(' ') > 0:
            word.replace(' ', '\" \"')
        word = urllib.parse.quote('\"' + word + '\"')
        url = github_url + word + '+' + searchIn + '+' + createdOrPushed + ':>' + day_str + '&sort=updated&order=desc'
        headers = {"Accept": "application/vnd.github.v3+json"}
        result = requests.get(url, timeout=10, headers=headers)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            codes = [{'repo':a['full_name'], 'repo:link':a['html_url'], 'created_at':a['created_at'], 'pushed_at':a['pushed_at'], 'description':a['description']} for a in resultdata['items'] if a['size'] > 0]
            self.setResultData(codes, filter='DROP', filter_target=['repo'], exclude_target=['repo'])
        else:
            self.setStatus('NG', comment='Status Code is {}'.format(str(statuscode)))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found repos about `{}`'.format(self.query['name'])]
            message += [x['repo:link'] for x in result]
        else:
            message = []
        return message
