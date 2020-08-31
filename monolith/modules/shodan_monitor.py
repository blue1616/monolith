from .monomodule import MonoModule

import requests
import datetime
import urllib.parse

description = '''This module searches SHODAN with Query.
Signle page result contains up to 100 hosts.
Hence, check your Query not to exceed signle page limitation.
https://www.shodan.io/

Practical SHODAN query list,
https://github.com/n0x08/ShodanTools
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'shodan'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = []
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['days'] = 8
        self.user_keys = [
            {'name': 'shodan_api_key', 'value': None, 'requred': True},
        ]

    def search(self):
        query = self.query['query']
        query = urllib.parse.quote_plus(query)
        shodan_api_key = self.getUserKey('shodan_api_key')
        api_endpoint = 'https://api.shodan.io'
        api_path = '/shodan/host/search'

        url = api_endpoint + api_path + '?key=' + shodan_api_key + '&query=' + query
        result = requests.get(url)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            hosts = []
            for host in resultdata['matches']:
                data = {}
                data['host'] = host['ip_str']
                data['port'] = host['port']
                data['timestamp'] = host['timestamp']
                data['country'] = host['location']['country_name']
                data['org'] = host['org']
                data['hostname'] = ','.join(host['hostnames'])
                data['domain'] = ','.join(host['domains'])
                data['data'] = host['data']
                data['host:link'] = 'https://www.shodan.io/host/' + data['host']
                hosts.append(data)
            self.setResultData(hosts, filter='DROP', filter_target=['host'], exclude_target=['host'])
        else:
            resultdata = result.text
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode), response=resultdata))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found new hosts about `{}`'.format(self.query['name'])]
            message += [x['host:link'] for x in result]
        else:
            message = []
        return message
