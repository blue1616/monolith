# -*- coding: utf-8 -*-

# API Token for Slackbot
# https://api.slack.com/bot-users
# CodeScraper uses lins05/slackbot (https://github.com/lins05/slackbot)
API_TOKEN = "XXXX-XXXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXX"

default_reply = "What you mean?"

# Do not edit
PLUGINS = [
    'monolithbot',
]

# Process to Search in Moules.
process_number = 2

enable_slackbot = True

modules = [
    'github_repository_search',
    'github_issues_search',
    'gist_search',
    'gitlab_repository_search',
    'google_custom_search',
    'rss_feed',
    'twitter_api',
    'shodan_monitor',
    'urlscan_monitor',
    'binaryedge_monitor',
    'newly_registered_domains',
    'urlhaus',
    'alienvault_pulse_search',
    'dnstwister',
    'passivetotal_ssl_cert',
    'passivetotal_subdomains',
#    'your_custom_module',
]

# Slack Cannels participating slackbot
# make channels and invete your slackbot
channels = [
    'General',
]

# Interval (Write in Crontab Format)
intervals = {
    'github_repository_search': '1 */1 * * *',
    'gist_search': '11 */1 * * *',
    'gitlab_repository_search': '21 */1 * * *',
    'google_custom_search': '31 */3 * * *',
    'rss_feed': '41 */1 * * *',
    'twitter_api': '52 */1 * * *',
    'shodan_monitor': '0 17 * * *',
    'urlscan_monitor': '6 */3 * * *',
    'binaryedge_monitor': '0 18 * * *',
    'newly_registered_domains': '0 9 * * *',
    'urlhaus': '0 9 * * *',
    'github_issues_search': '36 */1 * * *',
    'alienvault_pulse_search': '46 */1 * * *',
    'dnstwister': '0 0 * * *',
    'passivetotal_ssl_cert': '0 13 * * 2',
    'passivetotal_subdomains': '0 12 * * 2',
#    'your_custom_module': '* * * * *',
}

# Set Your API Keys.
user_keys = {
    'binaryedge_api_key': '',
    'google_custom_api_key': '',
    'google_custom_search_engine_id_1': '',
    'google_custom_search_engine_id_2': '',
    'shodan_api_key': '',
    'urlscan_api_key': '',
    'alienvault_api_key': '',
    'twitter_consumer_key': '',
    'twitter_consumer_secret': '',
    'twitter_access_token': '',
    'twitter_access_token_secret': '',
    'passivetotal_username': '',
    'passivetotal_secret_key': '',
}
