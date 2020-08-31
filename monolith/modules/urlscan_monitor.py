from .monomodule import MonoModule

import requests
import datetime
import urllib.parse

description = '''This module searches urlscan.io.

https://urlscan.io/search/#
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'urlscan'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = []
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['hours'] = 6
        self.user_keys = [
            {'name': 'urlscan_api_key', 'value': None, 'requred': True},
        ]

    def search(self):
        query = self.query['query']
        query = urllib.parse.quote_plus(query)
        urlscan_api_key = self.getUserKey('urlscan_api_key')
        api_endpoint = 'https://urlscan.io'
        api_path = '/api/v1/search/'
        headers = {'Content-Type': 'application/json', 'API-Key':urlscan_api_key }

        url = api_endpoint + api_path + '?q=' + query
        result = requests.get(url, headers=headers, timeout=10)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            urls = []
            for r in resultdata['results']:
                data = {}
                data['url'] = r['task']['url']
                data['timestamp'] = r['task']['time']
                data['ip'] = ''
                data['asn'] = ''
                data['country'] = ''
                if 'ip' in r['page'].keys():
                    data['ip'] = r['page']['ip']
                if 'asn' in r['page'].keys():
                    data['asn'] = r['page']['asn']
                if 'country' in r['page'].keys():
                    data['country'] = r['page']['country']
                data['result:link'] = r['result'].replace('api/v1/', '')
                urls.append(data)
            self.setResultData(urls, filter='DROP', filter_target=['url'], exclude_target=['url'])
        elif statuscode == 429:
            resultdata = result.text
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode), response=resultdata))
            self.enable_extra_interval = True
        else:
            resultdata = result.text
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode), response=resultdata))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found new url about `{}`'.format(self.query['name'])]
            for url in result:
                m = ''
                m += url['url'].replace(':', '[:]').replace('.', '[.]')
                m += '\n' + url['result:link']
                message.append(m)
        else:
            message = []
        return message
