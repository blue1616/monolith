from .monomodule import MonoModule

import requests
import datetime
import urllib.parse

description = '''This module searches binaryedge.
Set binaryedge query as a Query.

Signle page result contains up to 20 hosts.
Query help is here, https://docs.binaryedge.io/search/
and, practical queryies are in this project
https://github.com/balgan/binaryedge-cheatsheet'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'binaryedge'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = []
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['days'] = 8
        self.user_keys = [
            {'name': 'binaryedge_api_key', 'value': None, 'required': True},
        ]

    def search(self):
        query = self.query['query']
        query = urllib.parse.quote_plus(query)
        binaryedge_api_key = self.getUserKey('binaryedge_api_key')
        api_endpoint = 'https://api.binaryedge.io'
        api_path = '/v2/query/search'
        headers = {'X-Key':binaryedge_api_key}

        print(binaryedge_api_key)
        api_subscription = '/v2/user/subscription'
        url = api_endpoint + api_subscription
        result = requests.get(url, headers=headers)

        url = api_endpoint + api_path + '?query=' + query
        print(url)
        result = requests.get(url, headers=headers)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            hosts = []
            for host in resultdata['events']:
                data = {}
                data['host'] = host['target']['ip']
                data['port'] = host['target']['port']
                data['timestamp'] = host['origin']['ts']
                if 'service' in host['result']['data'].keys() and 'name' in host['result']['data']['service'].keys():
                    data['service'] = host['result']['data']['service']['name']
                else:
                    data['service'] = ''
                hosts.append(data)
            self.setResultData(hosts, filter='DROP', filter_target=['host'], exclude_target=['host'])
        else:
            resultdata = result.text
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode), response=resultdata))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found new hosts about `{}`'.format(self.query['name'])]
            message += [x['host'] for x in result]
        else:
            message = []
        return message
