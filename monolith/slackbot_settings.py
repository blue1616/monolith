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

# Enabled Module
modules = [
    'github_repository_search',
    'github_issues_search',
    'gist_search',
    'gitlab_repository_search',
    'google_custom_search',
    'rss_feed',
    'twitter',
    'shodan_monitor',
    'urlscan_monitor',
    'binaryedge_monitor',
    'newly_registered_domains',
    'urlhaus',
    'alienvault_pulse_search',
    'dnstwister',
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
    'twitter': '51 */1 * * *',
    'shodan_monitor': '0 17 * * *',
    'urlscan_monitor': '6 */3 * * *',
    'binaryedge_monitor': '0 18 * * *',
    'newly_registered_domains': '0 9 * * *',
    'urlhaus': '0 9 * * *',
    'github_issues_search': '36 */1 * * *',
    'alienvault_pulse_search': '46 */3 * * *',
    'dnstwister': '0 0 * * *',
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
}
