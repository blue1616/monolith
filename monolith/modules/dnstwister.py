from .monomodule import MonoModule

import binascii
import requests
import datetime
import urllib.parse
import time

description = '''This module searches dnstwister.
Set Domain Name as a Query.

https://dnstwister.report/
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'dnstwister'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = []
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['days'] = 2

    def resolve_ip(self, resolve_url):
        result = requests.get(resolve_url, timeout=10)
        time.sleep(1)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            return resultdata['ip']
        else:
            return ''

    def get_score(self, score_url):
        result = requests.get(score_url, timeout=10)
        time.sleep(1)
        statuscode = result.status_code
        score = {}
        if statuscode == 200:
            resultdata = result.json()
            score['redirects'] = resultdata['redirects']
            score['redirects_to'] = resultdata['redirects_to']
            score['score'] = resultdata['score']
            score['score_text'] = resultdata['score_text']
            return score
        else:
            return None

    def search(self):
        query = self.query['query']
        hexdecimal_domain = binascii.hexlify(query.encode('ascii')).decode('ascii')
        domain_fuzzer_url = 'http://dnstwister.report/api/fuzz/' + hexdecimal_domain

        result = requests.get(domain_fuzzer_url, timeout=10)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            domains = []
            count = 0
            for r in resultdata['fuzzy_domains']:
                data = {}
                data['domain'] = r['domain']
                data['fuzzer'] = r['fuzzer']
                data['resolve_ip_url'] = r['resolve_ip_url']
                data['parked_score_url'] = r['parked_score_url']
                domains.append(data)
                count += 1
            self.setResultData(domains, filter='DROP', filter_target=['domain', 'fuzzer'], exclude_target=['domain'])
            result = self.getCurrentResult()
            for r in result:
                r['resolved_ip'] = self.resolve_ip(r['resolve_ip_url'])
                score = self.get_score(r['parked_score_url'])
                if score != None:
                    r['redirects'] = score['redirects']
                    r['redirects_to'] = score['redirects_to']
                    r['score'] = score['score']
                    r['score_text'] = score['score_text']
                del r['resolve_ip_url'], r['parked_score_url'], r['__FILTERED_BY__']
            self.setResultData(result, filter=None, exclude=False)
        else:
            resultdata = result.text
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode), response=resultdata))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found domain about `{}`'.format(self.query['name'])]
            message += [x['domain'] for x in result]
        else:
            message = []
        return message
