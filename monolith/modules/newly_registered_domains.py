from .monomodule import MonoModule

import base64
import datetime
import os
import re
import requests
import zipfile

description = '''This Module get domain names newly registered from WHOISDS.
Search domain names contains Query String.

https://www.whoisds.com/newly-registered-domains
'''


class CustomModule(MonoModule):
    def set(self):
        self.name = 'new_domains'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = [
            {'name': 'method', 'value': 'STRING', 'choices':['STRING', 'REGEX'], 'alias': 'M'},
        ]
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['hours'] = 6

    def extractFile(self, zip_path, outdir):
        zip = zipfile.ZipFile(zip_path)
        zip.extractall(outdir)
        zip.close()
        os.remove(zip_path)

    def getNewlyRegisteredDomains(self, date, output_path):
        base64_date = base64.b64encode((date + '.zip').encode()).decode()
        url = 'https://www.whoisds.com/whois-database/newly-registered-domains/' + base64_date + '/nrd'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Trident/7.0; rv:11.0) like Gecko'}
        result = requests.get(url, headers=headers)
        statuscode = result.status_code
        if statuscode == 200:
            with open(output_path, 'wb') as f:
                f.write(result.content)
            return True
        else:
            return False

    def search(self):
        word = self.query['query']
        search_day = datetime.date.today() - datetime.timedelta(days=1)
        day_str = search_day.strftime('%Y-%m-%d')

        outputdir = os.path.join('data', self.name)
        zip_file_name = day_str + '.zip'
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        zip_file_path = os.path.join(outputdir, zip_file_name)
        domains_text = os.path.join(outputdir, day_str)
        domains_text = os.path.join(domains_text, 'domain-names.txt')
        if not os.path.exists(domains_text):
            if self.getNewlyRegisteredDomains(day_str, zip_file_path):
                self.extractFile(zip_file_path, os.path.join(outputdir, day_str))
            else:
                self.setStatus('NG', comment='Failed Download file...')

        results = []
        with open(domains_text, 'r') as f:
            domains = f.readlines()
            method = self.getParam('method')
            for domain in domains:
                if method == 'STRING':
                    if word.find('*') < 0:
                        word = '*' + word + '*'
                    if self.isMatched(word, domain):
                        results.append(domain)
                elif method == 'REGEX':
                    patt = re.compile(word)
                    if patt.match(domain):
                        results.append(domain)
        self.setResultData([{'domain': x} for x in results], filter='DROP', filter_method=method)

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found Newlay Registered Domains about `{}`'.format(self.query['name'])]
            message += [x['domain'] for x in result]
        else:
            message = []
        return message
