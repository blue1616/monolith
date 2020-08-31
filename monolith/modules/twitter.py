from .monomodule import MonoModule

from dateutil import parser, tz
import requests
import datetime
from pyquery import PyQuery
import re
import urllib.parse

from lxml.etree import tostring

description = '''This module searches Twitter.
This module isn't requres Twitter API.
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'twitter'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = [
            {'name': 'users', 'value': ''},
            {'name': 'min_faves', 'value': ''},
            {'name': 'min_retweets', 'value': ''},
        ]
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = ''
        self.default_query['channel'] = ''
        self.extra_interval['hours'] = 6

    def parseTweets(self, items_html):
        tweetslist = []
        scraped_tweets = PyQuery(items_html)
        scraped_tweets.remove('div.withheld-tweet')
        tweets = scraped_tweets('div.js-stream-tweet')
        if len(tweets) != 0:
            for tweet_html in tweets:
                t = {}
                tweetPQ = PyQuery(tweet_html)
                t['user'] = tweetPQ("span:first.username.u-dir b").text()
                txt = re.sub(r"\s+", " ", tweetPQ("p.js-tweet-text").text())
                txt = txt.replace('# ', '#')
                txt = txt.replace('@ ', '@')
                t['tweet'] = txt
                t['id'] = tweetPQ.attr("data-tweet-id")
                t['retweets'] = int(tweetPQ("span.ProfileTweet-action--retweet span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""))
                t['favorites'] = int(tweetPQ("span.ProfileTweet-action--favorite span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""))
                t[':link'] = 'https://twitter.com' + tweetPQ.attr("data-permalink-path")
                t['timestamp'] = int(tweetPQ("small.time span.js-short-timestamp").attr("data-time"))
                if not tweetPQ('.Icon--promoted'):
                    tweetslist.append(t)
        return tweetslist

    def search(self):
        query = ''
        word = self.query['query']
        if word.strip() != '':
            query += word
        users = self.getParam('users')
        if type(users) == str and users.strip() != '':
            if users.find(',') >= 0:
                user = [x.strip() for x in users.split(',')]
                query += ' from:' + ' OR from:'.join(user)
            else:
                query += ' from:' + users.strip()
        min_faves = str(self.getParam('min_faves'))
        if type(min_faves) == str and min_faves.isdigit():
            query += ' min_faves:' + min_faves
        min_retweets = str(self.getParam('min_retweets'))
        if type(min_retweets) == str and min_retweets.isdigit():
            query += ' min_retweets:' + min_retweets
        query = urllib.parse.quote_plus(query)
        url = 'https://twitter.com/i/search/timeline?f=tweets&q={query}&src=typd'.format(query=query)
        headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0',
            'Accept':"application/json, text/javascript, */*; q=0.01",
            'Accept-Language':"de,en-US;q=0.7,en;q=0.3",
            'X-Requested-With':"XMLHttpRequest",
            'Referer':url,
            'Connection':"keep-alive"
        }
        response = requests.get(url, headers=headers)
        statuscode = response.status_code
        tweetslist = []
        new_tweets = []
        res = response.json()
        if statuscode == 200:
            json_response = response.json()
            tweetslist = []
            if json_response['items_html'].strip() != '':
                tweetslist = self.parseTweets(json_response['items_html'])
            self.setResultData(tweetslist, filter='DROP', filter_target=['tweet'], exclude_target=['id'])
        else:
            self.setStatus('NG', comment='Status Code is {}'.format(str(statuscode)))

    def createMessage(self):
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found tweets about `{}`'.format(self.query['name'])]
            for tw in result:
                m = ''
                m += tw[':link']
                m += ' (FROM: '+ tw['user'] + ')\n'
                m += '>>>' + tw['tweet'] + '\n'
                message.append(m)
        else:
            message = []
        return message
