from .monomodule import MonoModule

import datetime
import json
import requests
import urllib.parse

description = '''RiskIQ Passivet Total Search.
Search for an SSL certificate and list the hosts where that certificate has been observed.

https://api.passivetotal.org/index.html
'''
allowed_filed = [
    "issuerSurname",
    "subjectOrganizationName",
    "issuerCountry",
    "issuerOrganizationUnitName",
    "fingerprint",
    "subjectOrganizationUnitName",
    "serialNumber",
    "subjectEmailAddress",
    "subjectCountry",
    "issuerGivenName",
    "subjectCommonName",
    "issuerCommonName",
    "issuerStateOrProvinceName",
    "issuerProvince",
    "subjectStateOrProvinceName",
    "sha1",
    "subjectStreetAddress",
    "subjectSerialNumber",
    "issuerOrganizationName",
    "subjectSurname",
    "subjectLocalityName",
    "issuerStreetAddress",
    "issuerLocalityName",
    "subjectGivenName",
    "subjectProvince",
    "issuerSerialNumber",
    "issuerEmailAddress"
]

class CustomModule(MonoModule):
    def set(self):
        self.name = 'passivetotal_ssl_cert'
        self.module_description = description
        self.default_query['module'] = self.name
        self.default_query['module_description'] = self.module_description
        self.default_query['params'] = [
            {'name': 'Field', 'value': 'issuerCommonName', 'choices':allowed_filed, 'alias': 'F'},
        ]
        self.default_query['expire_date'] = ''
        self.default_query['enable'] = True
        self.default_query['channel'] = ''
        self.extra_interval['minutes'] = 4
        self.max_error_count = 4
        self.user_keys = [
            {'name': 'passivetotal_username', 'value': None, 'required': True},
            {'name': 'passivetotal_secret_key', 'value': None, 'required': True},
        ]

    def getSSLCert(self, field, query):
        data = {'field': field, 'query': query}
        username = self.getUserKey('passivetotal_username')
        key = self.getUserKey('passivetotal_secret_key')
        auth = (username, key)
        resource = 'ssl-certificate/search'
        url = 'https://api.passivetotal.org/v2/' + resource
        result = requests.get(url, auth=auth, json=data)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            return statuscode, [cert['sha1'] for cert in resultdata['results']]
        else:
            return statuscode, None

    def getCertHistory(self, hash):
        data = {'query': hash}
        username = self.getUserKey('passivetotal_username')
        key = self.getUserKey('passivetotal_secret_key')
        auth = (username, key)
        resource = 'ssl-certificate/history'
        url = 'https://api.passivetotal.org/v2/' + resource
        result = requests.get(url, auth=auth, json=data)
        statuscode = result.status_code
        if statuscode == 200:
            resultdata = result.json()
            hosts = []
            for cert in resultdata['results']:
                if 'ipAddresses' in cert:
                    for ip in cert['ipAddresses']:
                        host = {}
                        host['ip'] = ip
                        host['cert_sha1'] = cert['sha1']
                        host['firstSeen'] = cert['firstSeen']
                        host['lastSeen'] = cert['lastSeen']
                        hosts.append(host)
            return statuscode, hosts
        else:
            return statuscode, None

    def search(self):
        query = self.query['query']
        field = self.getParam('Field')
        statuscode, certs_hash = self.getSSLCert(field, query)
        if statuscode == 200:
            print(certs_hash)
            result_hosts = []
            for cert in certs_hash:
                statuscode, hosts = self.getCertHistory(cert)
                print(hosts)
                if statuscode != 200:
                    self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode)))
                    break
                result_hosts += hosts
            self.setResultData(result_hosts, filter='DROP', filter_target=['ip', 'cert_sha1'], exclude_target=['ip'])
        else:
            resultdata = result.text
            self.setStatus('NG', comment='Status Code is {code}.\n{response}'.format(code=str(statuscode)))

    def createMessage(self):
        message = []
        result = self.getCurrentResult()
        if len(result) != 0:
            message = ['I found host about `{}`'.format(self.query['name'])]
            message += [x['ip'] for x in result]
        else:
            message = []
        return message
