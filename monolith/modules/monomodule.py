import datetime
import re
import time
import traceback

class MonoModule:
    def __init__(self):
        self.name = ''
        self.module_description = ''
        self.query = {}
        self.default_query = {
            'module': self.name,
            'module_description': self.module_description,
            'name': '',
            'query': '',
            'params': [],
            'expire_date': '',
            'exclude_list': {},
            'filters': [],
            'enable': True,
            'channel': '',
        }
        self.user_keys = []
        self.sleep_time = 10
        self.__enable = True
        self.__result = {}
        self.run_interval = '0 0 1 * *'
        self.enable_extra_interval = False
        self.extra_interval = {
            'days': 0,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
        }
        self.max_error_count = 10
        self.not_notify_at_first_time = True
        self.__exclude_list = {}
        self.updateQuery = {}

    def set(self):
        self.__init__()

    def initModule(self):
        self.query = {}
        self.user_keys = []
        self.enable_extra_interval = False
        self.__exclude_list = {}
        self.updateQuery = {}
        self.__result = {}

    def getDefaultQuery(self):
        default_query = self.default_query
        default_query['index'] = 0
        default_query['name'] = '__DEFAULT_SETTING__'
        default_query['__MOD_ENABLE__'] = self.__enable
        default_query['__INITIAL__'] = True
        default_query['__SAFETY__'] = 0
        return default_query

    def getParam(self, param_name):
        params = self.query['params']
        param = [x['value'] for x in params if x['name'] == param_name]
        if len(param) > 0:
            return param[0]
        else:
            return None

    def getUserKey(self, name):
        key = [x for x in self.user_keys if x['name'] == name]
        if len(key) > 0:
            return key[0]['value']
        else:
            return None

    def createMessage(self):
        return []

    def search(self):
        pass

    def run(self, query, timestamp):
        self.__result = {}
        self.__result['module_start'] = timestamp
        self.__result['module'] = self.name
        self.__result['query_id'] = query['index']
        self.__result['query_name'] = query['name']
        self.query = query
        status_data = {}
        try:
            self.search()
        except:
            status_data['status'] = 'Error'
            status_data['error_message'] = traceback.format_exc()
            self.__result['status'] = status_data
        if not 'status' in self.__result:
            status_data['status'] = 'OK'
            self.__result['status'] = status_data
        time.sleep(self.sleep_time)

    def isMatched(self, patterm, text):
        pos_e = patterm.find('*')
        if pos_e < 0:
            if patterm == text:
                return True
            else:
                return False
        sub = patterm[:pos_e]
        if not text.startswith(sub):
            return False
        pos_s = pos_e + 1
        pos_e = patterm.find('*', pos_s)
        text_pos = len(sub)
        while pos_e >= 0:
            sub = patterm[pos_s:pos_e]
            if text.find(sub, text_pos) < 0:
                return False
            else:
                text_pos = text.find(sub, text_pos) + len(sub)
            pos_s = pos_e + 1
            pos_e = patterm.find('*', pos_s)
        sub = patterm[pos_s:]
        if not text[text_pos:].endswith(sub):
            return False
        return True

    def applyFilter(self, method='STRING', target=[]):
        for result in self.__result['result']:
            if target == []:
                target_values = [str(x) for x in result.values()]
            else:
                target_values = [str(result[x]) for x in target if x in result.keys()]
            matched_filter = []
            for f in self.query['filters']:
                if method == 'STRING':
                    matched = False
                    for t_v in target_values:
                        if self.isMatched(f['filter'], t_v):
                            matched = True
                            break
                    if matched:
                        matched_filter.append(f['id'])
                if method == 'REGEX':
                    matched = False
                    patt = re.compile(f['filter'])
                    for t_v in target_values:
                        if patt.match(t_v):
                            matched = True
                            break
                    if matched:
                        matched_filter.append(f['id'])
            result['__FILTERED_BY__'] = matched_filter

    def dropFiltered(self):
        self.__result['result'] = [x for x in self.__result['result'] if x['__FILTERED_BY__'] == []]

    def pickFiltered(self):
        if len(self.query['filters']) > 0:
            self.__result['result'] = [x for x in self.__result['result'] if x['__FILTERED_BY__'] != []]

    def updateExcludeList(self, target=[]):
        exclude_list = {}
        for result in self.__result['result']:
            for k,v in result.items():
                if target == [] or k in target:
                    if k in exclude_list.keys():
                        exclude_list[k].append(v)
                    else:
                        exclude_list[k] = [v]
        self.__exclude_list = exclude_list

    def getExcludeList(self):
        return self.__exclude_list

    def applyExcludeList(self):
        exclude_list = self.query['exclude_list']
        matched_result = []
        for result in self.__result['result']:
            matched = False
            for k,v in result.items():
                if k in exclude_list.keys() and v in exclude_list[k]:
                    matched = True
            if not matched:
                matched_result.append(result)
        self.__result['result'] = matched_result

    def setResultData(self, result_data, filter='DROP', filter_method='STRING', filter_target=[], exclude=True, exclude_target=[]):
        self.__result['result'] = result_data
        if len(result_data) != 0:
            self.__result['result_header'] = list(result_data[0].keys())
        else:
            self.__result['result_header'] = []
        if filter in ['DROP', 'PICK']:
            self.applyFilter(method=filter_method, target=filter_target)
            if filter == 'DROP':
                self.dropFiltered()
            else:
                self.pickFiltered()
        if exclude:
            self.updateExcludeList(exclude_target)
            self.applyExcludeList()
        self.__result['result_count'] = len(self.__result['result'])

    def setStatus(self, status, comment=''):
        status_data = {}
        status_data['status'] = status
        status_data['comment'] = comment
        self.__result['status'] = status_data

    def getCurrentResult(self):
        if 'result' in self.__result:
            return self.__result['result']
        else:
            return []

    def getResult(self):
        return self.__result
