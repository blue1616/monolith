from .monomodule import MonoModule

import requests
import lxml.html
import datetime
import urllib.parse

description = '''This module searches gist snippet.
Set search keyword as a Query.

https://gist.github.com/search'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'gist'
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
        search_day = datetime.date.today() - datetime.timedelta(2)
        day_str = search_day.strftime('%Y-%m-%d')
        url = 'https://gist.github.com/search?utf8=%E2%9C%93&q=' + word + '+created%3A>' + day_str + '&ref=searchresults'
        result = requests.get(url, timeout=10)
        statuscode = result.status_code
        root = lxml.html.fromstring(result.text)
        if statuscode == 200:
            codes = [{'gist:link':a.get('href')} for a in root.xpath('//div/a[@class="link-overlay"]')]
            self.setResultData(codes, filter='DROP', filter_target=['gist:link'], exclude_target=['gist:link'])
        else:
            self.setStatus('NG', comment='Status Code is {}'.format(str(statuscode)))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found gist about `{}`'.format(self.query['name'])]
            message += [x['gist:link'] for x in result]
        else:
            message = []
        return message
