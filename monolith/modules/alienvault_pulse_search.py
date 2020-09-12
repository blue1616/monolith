from .monomodule import MonoModule

import requests
import datetime
import re
import urllib.parse

description = '''This module searches AlienVault Pulse.
Set search keyword as a Query.

https://otx.alienvault.com/api
'''


class CustomModule(MonoModule):
    def set(self):
        self.name = 'alienvault_pulse'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = [
            {'name': 'CreatedOrModified', 'value': 'modified', 'choices':['created','modified'], 'alias': 'CM'},
        ]
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['hours'] = 6
        self.user_keys = [
            {'name': 'alienvault_api_key', 'value': None, 'requred': True},
        ]

    def search(self):
        word = self.query['query']
        word = urllib.parse.quote_plus('\"' + word + '\" ')
        sort = self.getParam('CreatedOrModified')
        if sort == None:
            sort = 'created'
        api_endpoint = 'https://otx.alienvault.com'
        api_path = '/api/v1/search/pulses'
        api_path += '?limit=10'
        api_path += '&q=' + word
        api_path += '&sort=' + sort
        url = api_endpoint + api_path
        alienvault_api_key = self.getUserKey('alienvault_api_key')
        headers = {'X-OTX-API-KEY': alienvault_api_key}
        result = requests.get(url, headers=headers)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            pulses = []
            for r in resultdata['results']:
                data = {}
                data['id'] = r['id']
                data['name'] = r['name']
                data['description'] = r['description']
                data['created'] = r['created']
                data['modified'] = r['modified']
                contents = {}
                for indicator in r['indicators']:
                    type = indicator['type']
                    if type in contents.keys():
                        contents[type].append(indicator['indicator'])
                    else:
                        contents[type] = [indicator['indicator']]
                summary = []
                for k,v in contents.items():
                    summary.append(k + ':' + str(len(v)))
                data['summary'] = ', '.join(summary)
                data['pulse:link'] = 'https://otx.alienvault.com/pulse/' + data['id']
                pulses.append(data)
            self.setResultData(pulses, filter='DROP', filter_target=['name', 'description'], exclude_target=['id'])
        else:
            resultdata = result.text
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode), response=resultdata))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found AlienVault Pulse about `{}`'.format(self.query['name'])]
            message += [x['pulse:link'] for x in result]
        else:
            message = []
        return message
