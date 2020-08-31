from .monomodule import MonoModule

from dateutil import parser, tz
import datetime
import feedparser
import lxml.html
import requests
import urllib.parse
import time

description = '''This module gets RSS feed.
Set RSS feed url(v1/v2/atom) to Query.
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'rss'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = [
            {'name': 'FilterType', 'value': 'DROP', 'choices':['DROP', 'PICK'], 'alias': 'FT'},
        ]
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['hours'] = 6

    def checkRSSUrl(self, url):
        try:
            headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0'}
            response = requests.get(url, timeout=4, headers=headers)
            rss = feedparser.parse(response.text)
            rssurl = None
            if rss['version'] == 'rss10' or rss['version'] == 'rss20' or rss['version'] == 'atom10':
                rssurl = url
            else:
                root = lxml.html.fromstring(response.text)
                for link in root.xpath('//link[@type="application/rss+xml"]'):
                    url = link.get('href')
                rss = feedparser.parse(url)
                if rss['version'] == 'rss10' or rss['version'] == 'rss20' or rss['version'] == 'atom10':
                    rssurl = url
            return rssurl
        except:
            return None

    def parseRSS(self, items):
        parseddata = []
        for item in items:
            data = {
              ':link' : item['link']
            }
            if 'title' in item.keys():
                data['title'] = item['title']
            if 'summary' in item.keys():
                data['summary'] = item['summary']
            if 'updated' in item.keys() and item['updated'] != '':
                dt = parser.parse(item['updated'])
                if dt.tzinfo == None:
                    data['timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    data['timestamp'] = dt.astimezone(tz.tzutc()).strftime('%Y-%m-%d %H:%M:%S')
            elif 'published' in item.keys() and item['published'] != '':
                dt = parser.parse(item['published'])
                if dt.tzinfo == None:
                    data['timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    data['timestamp'] = dt.astimezone(tz.tzutc()).strftime('%Y-%m-%d %H:%M:%S')
            else:
                data['timestamp'] = None
            taglist = []
            if 'tags'in item.keys():
                for tag in item['tags']:
                    taglist.append(tag['term'])
            data['tags'] = taglist
            contents = []
#            if 'content'in item.keys():
#                for c in item['content']:
#                    content = (c['type'], c['value'])
#                    contents.append(content)
#            data['contents'] = contents
            parseddata.append(data)
        return parseddata

    def search(self):
        url = self.query['query']
        filter_type = self.getParam('FilterType')
        if not filter_type in ['DROP', 'PICK']:
            filter_type = 'DROP'
        headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0'}
        if self.query['__INITIAL__']:
            rssurl = self.checkRSSUrl(url)
            if rssurl == None:
                self.setStatus('NG', comment='RSS URL is Invalid.')
                self.updateQuery = {
                    'enable': False
                }
                return
            elif rssurl != url:
                url = rssurl
                self.updateQuery = {
                    'query': rssurl
                }
            time.sleep(10)
        response = requests.get(url, timeout=10, headers=headers)
        updateditems = []
        statuscode = response.status_code
        if statuscode == 200:
            rss = feedparser.parse(response.text)
            result = self.parseRSS(rss['entries'])
            self.setResultData(result, filter=filter_type, filter_target=['title', 'summary', 'tags'], exclude_target=[':link', 'timestamp'])
        else:
            self.setStatus('NG', comment='Status Code is {}'.format(str(statuscode)))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found feed about `{}`'.format(self.query['name'])]
            message += [x[':link'] for x in result]
        else:
            message = []
        return message
