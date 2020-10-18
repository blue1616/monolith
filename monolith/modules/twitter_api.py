from .monomodule import MonoModule

import json
import requests
import datetime
from requests_oauthlib import OAuth1Session

description = '''This module searches Twitter with Twitter API.
https://developer.twitter.com/en/docs/twitter-api/v1/tweets/search/api-reference/get-search-tweets

This module reqires Twitter API.
Access here,
https://developer.twitter.com/en
and, get Consumer API key, Consumer API secret key, Access token, and Access token secret.

Set search keyword as a Query.

When adding a user to the search condition, use the users parameter.
You can specify multiple users by separating them with ",".
'''

class CustomModule(MonoModule):
    def set(self):
        self.name = 'twitter_api'
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
        self.user_keys = [
            {'name': 'twitter_consumer_key', 'value': None, 'requred': True},
            {'name': 'twitter_consumer_secret', 'value': None, 'requred': True},
            {'name': 'twitter_access_token', 'value': None, 'requred': True},
            {'name': 'twitter_access_token_secret', 'value': None, 'requred': True},
        ]

    def search(self):
        consumer_key = self.getUserKey('twitter_consumer_key')
        consumer_secret = self.getUserKey('twitter_consumer_secret')
        access_token = self.getUserKey('twitter_access_token')
        access_token_secret = self.getUserKey('twitter_access_token_secret')
        twitter = OAuth1Session(consumer_key, consumer_secret, access_token, access_token_secret)
        query = ''
        word = self.query['query']
        if word.strip() != '':
            query += word
        users = self.getParam('users')
        if type(users) == str and users.strip() != '':
            if users.find(',') >= 0:
                user = [x.strip() for x in users.split(',') if x.strip() != '']
                query += ' from:' + ' OR from:'.join(user)
            else:
                query += ' from:' + users.strip()
        min_faves = str(self.getParam('min_faves'))
        if type(min_faves) == str and min_faves.isdigit():
            query += ' min_faves:' + min_faves
        min_retweets = str(self.getParam('min_retweets'))
        if type(min_retweets) == str and min_retweets.isdigit():
            query += ' min_retweets:' + min_retweets
        params ={
            'count': 20,
            'q': query,
            'result_type': 'recent'
        }
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        response = twitter.get(url, params=params)
        statuscode = response.status_code
        if statuscode == 200:
            tweetslist = []
            json_response = response.json()
            for tweet in json_response['statuses']:
                data = {}
                data['id'] = tweet['id']
                data['created_at'] = tweet['created_at']
                data['user'] = tweet['user']['screen_name']
                data['tweet'] = tweet['text']
                data['retweets'] = tweet['retweet_count']
                data['favorites'] = tweet['favorite_count']
                data[':link'] = 'https://twitter.com/' + data['user'] + '/status/' + str(data['id'])
                tweetslist.append(data)
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
                m += '>>' + tw['tweet'] + '\n'
                message.append(m)
        else:
            message = []
        return message
