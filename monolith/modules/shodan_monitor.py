from .monomodule import MonoModule

import requests
import datetime
import time
import urllib.parse

description = '''This module searches SHODAN with Query.
Set SHODAN query as a Query.

Signle page result contains up to 100 hosts.
If you want to get more results, change the max_pages parameter (default: 1).
https://www.shodan.io/

Practical SHODAN queries are int this project,
https://github.com/n0x08/ShodanTools
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'shodan'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = [
            {'name': 'max_pages', 'value': '1'},
        ]
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['days'] = 8
        self.user_keys = [
            {'name': 'shodan_api_key', 'value': None, 'required': True},
        ]

    def search_shodan(self, ):
        pass

    def search(self):
        query = self.query['query']
        query = urllib.parse.quote_plus(query)
        max_pages = self.getParam('max_pages')
        if type(max_pages) == str and max_pages.isdecimal():
            max_pages = int(max_pages)
        else:
            max_pages = 1
        shodan_api_key = self.getUserKey('shodan_api_key')
        api_endpoint = 'https://api.shodan.io'
        api_path = '/shodan/host/search'

        page = 1
        isNG = False
        hosts = []

        while page <= max_pages:
            print('page:' + str(page))
            url = api_endpoint + api_path + '?key=' + shodan_api_key + '&query=' + query + '&page=' + str(page)
            result = requests.get(url)
            statuscode = result.status_code
            if statuscode == 200:
                resultdata = result.json()
                total_count = resultdata['total']
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
                if len(resultdata['matches']) == 0 or total_count <= len(hosts):
                    break
            else:
                isNG = True
                resultdata = result.text
                break
            time.sleep(1)
            page += 1
        self.setResultData(hosts, filter='DROP', filter_target=['host', 'hostname', 'domain'], exclude_target=['host'])
        if isNG:
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode), response=resultdata))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found new hosts about `{}`'.format(self.query['name'])]
            message += [x['host:link'] for x in result]
        else:
            message = []
        return message
