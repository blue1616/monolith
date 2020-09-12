from .monomodule import MonoModule

import requests
import datetime
import urllib.parse

description = '''This module searches with prepared google custom search.
Set search keyword as a Query.

Google Custom Search is required API key and search engine id.
Google Custom Search API : https://developers.google.com/custom-search/v1/overview
Access here : https://console.developers.google.com/
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'google_custom'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = [
            {'name': 'searchEngineId', 'value': '1', 'choices':['1', '2', '3', '4'], 'alias': 'SE'},
        ]
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['hours'] = 12
        self.user_keys = [
            {'name': 'google_custom_api_key', 'value': None, 'requred': True},
            {'name': 'google_custom_search_engine_id_1', 'value': None, 'requred': False},
            {'name': 'google_custom_search_engine_id_2', 'value': None, 'requred': False},
            {'name': 'google_custom_search_engine_id_3', 'value': None, 'requred': False},
            {'name': 'google_custom_search_engine_id_4', 'value': None, 'requred': False},
        ]

    def search(self):
        word = self.query['query']
        if word.find(' ') > 0:
            word.replace(' ', '\" \"')
        word = urllib.parse.quote('\"' + word + '\"')
        headers = {"content-type": "application/json"}
        google_custom_api_key = self.getUserKey('google_custom_api_key')
        google_custom_search_engine_id = None
        engine_id = self.getParam('searchEngineId')
        if engine_id in ['1', '2', '3', '4']:
            google_custom_search_engine_id = self.getUserKey('google_custom_search_engine_id_' + engine_id)
        if google_custom_search_engine_id == None or google_custom_search_engine_id == '':
            self.setStatus('NG', comment='Search Engine ID missed. Disable Query.')
            self.updateQuery = {
                'enable': False
            }
            return
        url = 'https://www.googleapis.com/customsearch/v1?key=' + google_custom_api_key + '&rsz=filtered_cse&num=10&hl=en&prettyPrint=false&cx=' + google_custom_search_engine_id + '&q=' + word + '&sort=date'
        result = requests.get(url, timeout=10, headers=headers)
        statuscode = result.status_code
        codes = {}
        if statuscode == 200:
            jsondata = result.json()
            codes = []
            if 'items' in jsondata.keys():
                for item in jsondata['items']:
                    code = {
                        'title': '',
                        'snippet': '',
                        ':link': '',
                    }
                    if 'title' in item.keys():
                        code['title'] = item['title']
                    if 'snippet' in item.keys():
                        code['snippet'] = item['snippet']
                    if 'link' in item.keys():
                        code[':link'] = item['link']
                    codes.append(code)
            self.setResultData(codes, filter='DROP', exclude_target=[':link'])
        else:
            self.setStatus('NG', comment='Status Code is {}'.format(str(statuscode)))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found sites about `{}`'.format(self.query['name'])]
            message += [x[':link'] for x in result]
        else:
            message = []
        return message
