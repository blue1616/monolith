#from util.dbHelper import Helper

import datetime
from importlib import import_module
import json
import slackbot_settings

test_modules = 'passivetotal_ssl_cert'

mod = import_module('.' + test_modules, 'modules')
module = mod.CustomModule()
module.set()

query = module.default_query
query['index'] = -1
query['name'] = 'test_query'
query['query'] = 'test'
query['params'] = [
    {'name': 'Resource', 'value': 'whois/search', 'choices':['enrichment/subdomains', 'whois/search' ,'ssl-certificate/search'], 'alias': 'R'},
    {'name': 'Field', 'value': 'issuerCommonName', 'alias': 'F'},
]

print(module.name)
timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
module.sleep_time = 1
for key in module.user_keys:
    if key['name'] in slackbot_settings.user_keys.keys():
        key['value'] = slackbot_settings.user_keys[key['name']]
module.run(query, timestamp)
print('---PRINT RESULTS---')
count = 1
results = module.getResult()
print('---STATUS---')
print(results['status']['status'])
if results['status']['status'] == 'Error':
    print(results['status']['error_message'])
elif results['status']['status'] == 'NG':
    print(results['status']['comment'])
else:
    for result in module.getCurrentResult():
        print('---Result {}---'.format(str(count)))
        for k, v in result.items():
            print('  ' + str(k) + ' : ' + str(v))
        count += 1

print('---NOTIFICATION MESSAGES---')
messages = module.createMessage()
for message in messages:
    print(message)
