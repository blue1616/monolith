from .monomodule import MonoModule

import datetime
import json
import requests
import urllib.parse

description = '''RiskIQ Passivet Total Search.
Search for a domain name and list subdomains.

https://api.passivetotal.org/index.html
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'passivetotal_subdomains'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = []
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['minutes'] = 4
        self.max_error_count = 4
        self.user_keys = [
            {'name': 'passivetotal_username', 'value': None, 'required': True},
            {'name': 'passivetotal_secret_key', 'value': None, 'required': True},
        ]

    def search(self):
        query = self.query['query']
        data = {'query': query}
        username = self.getUserKey('passivetotal_username')
        key = self.getUserKey('passivetotal_secret_key')
        auth = (username, key)
        resource = 'enrichment/subdomains'
        url = 'https://api.passivetotal.org/v2/' + resource
        result = requests.get(url, auth=auth, json=data)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            results = [{'subdomain': subdomain + '.' + query} for subdomain in resultdata['subdomains']]
            self.setResultData(results, filter='DROP', filter_target=['subdomain'], exclude_target=['subdomain'])
        else:
            resultdata = result.text
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode), response=resultdata))

    def createMessage(self):
        message = []
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found subdomain about `{}`'.format(self.query['name'])]
            message += [x['subdomain'] for x in result]
        else:
            message = []
        return message
