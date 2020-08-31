from .monomodule import MonoModule

import requests
import datetime
import lxml.html
import urllib.parse

description = '''This module searches gitlab repository.

https://gitlab.com/explore/projects
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'gitlab'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = []
        self.default_query['expire_date'] = 180
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['hours'] = 6

    def search(self):
        word = self.query['query']
        if word.find(' ') > 0:
          word.replace(' ', '\" \"')
        word = urllib.parse.quote('\"' + word + '\"')
        url = 'https://gitlab.com/explore/projects?utf8=%E2%9C%93&name=' + word + '&sort=latest_activity_desc'
        result = requests.get(url, timeout=10)
        statuscode = result.status_code
        root = lxml.html.fromstring(result.text)
        if statuscode == 200:
            codes = [{'repo':a.get('href'), 'repo:link':'https://gitlab.com' + a.get('href')} for a in root.xpath('//div/a[@class="project"]')]
            self.setResultData(codes, filter='DROP', filter_target=['repo'], exclude_target=['repo'])
        else:
            self.setStatus('NG', comment='Status Code is {}'.format(str(statuscode)))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found repos about `{}`'.format(self.query['name'])]
            message += ['https://gitlab.com' + x['repo'] for x in result]
        else:
            message = []
        return message
