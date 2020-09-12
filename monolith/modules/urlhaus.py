from .monomodule import MonoModule

import datetime
import os
import requests

description = '''This Module get malware URLs from the URLhaus database.
Search for tags and URLs by setting keyword as a Query.

https://urlhaus.abuse.ch/api/
'''


class CustomModule(MonoModule):
    def set(self):
        self.name = 'urlhaus'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = []
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['days'] = 3

    def downloadUrlList(self, output_path):
        print('Download CSV File')
        url = 'https://urlhaus.abuse.ch/downloads/csv_recent/'
        result = requests.get(url)
        statuscode = result.status_code
        if statuscode == 200:
            with open(output_path, 'w') as f:
                f.write(result.text)
            return True
        else:
            return False

    def search(self):
        word = self.query['query']
        search_from = datetime.datetime.now() - datetime.timedelta(days=1)
        csv_file_name = datetime.date.today().strftime('%Y-%m-%d') + '.csv'
        outputdir = os.path.join('data', self.name)
        csv_file_path = os.path.join(outputdir, csv_file_name)
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        succeeded = True
        if not os.path.exists(csv_file_path):
            for old_file in os.listdir(outputdir):
                if old_file.endswith('.csv'):
                    os.remove(os.path.join(outputdir, old_file))
            succeeded = self.downloadUrlList(csv_file_path)
        if succeeded:
            urls = []
            with open(csv_file_path, 'r') as f:
                for row in f.readlines():
                    if not row.startswith('#'):
                        columns = row[1:-1].split('","')
                        data = {}
                        data['id'] = columns[0]
                        data['dateadded'] = columns[1]
                        data['url'] = columns[2]
                        data['url_status'] = columns[3]
                        data['threat'] = columns[4]
                        data['tags'] = columns[5]
                        data['urlhaus:link'] = columns[6]
                        data['reporter'] = columns[7]
                        detected_time = datetime.datetime.strptime(data['dateadded'], '%Y-%m-%d %H:%M:%S')
                        if (data['tags'].find(word) >= 0 or data['url'].find(word) >= 0) and search_from < detected_time:
                            urls.append(data)
            self.setResultData(urls, filter='DROP', filter_target=['url'], exclude_target=['id'])
        else:
            self.setStatus('NG', comment='File Donwload Error.')

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found new url about `{}`'.format(self.query['name'])]
            for url in result:
                m = ''
                m += url['url'].replace(':', '[:]').replace('.', '[.]')
                m += '\n' + url['urlhaus:link']
                message.append(m)
        else:
            message = []
        return message
