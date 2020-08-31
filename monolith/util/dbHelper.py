import datetime
from crontab import CronTab
import logging
import math
from pymongo import MongoClient, errors
import re

class Helper:
    client = None
    db = None
    config_collection = None
    result_collection = None
    job_collection = None

    def __init__(self, BD_HOST, DB_PORT, DB_NAME):
        self.client = MongoClient(BD_HOST, DB_PORT)
        self.db = self.client[DB_NAME]
        self.config_collection = self.db['config']
        self.result_collection = self.db['result']
        self.job_collection = self.db['job']

    def validateModule(self, config):
        if type(config) == dict:
            if not 'module' in config.keys():
                return False
            if not '__MOD_ENABLE__' in config.keys():
                return False
            if not '__INITIAL__' in config.keys():
                return False
            if not '__SAFETY__' in config.keys():
                return False
            if 'params' in config.keys():
                if type(config['params']) != list:
                    return False
                if len(set([x['name'] for x in config['params']])) != len(config['params']):
                    return False
                for param in config['params']:
                    if type(param) != dict:
                        return False
                    if not 'name' in param.keys():
                        return False
                    if not 'value' in param.keys():
                        return False
                    if 'choices' in param.keys():
                        if not param['value'] in param['choices']:
                            return False
        else:
            return False
        return True

    def getModuleName(self):
        mame = []
        for cur in self.job_collection.find({}):
            if 'module' in cur.keys():
                mame.append(cur['module'])
        return sorted(list(set(mame)))

    # Control Global Config
    def setGlobalConfig(self, slackbot_api_token, channels, user_keys):
        global_setting = {
            'module': '__GLOBAL__',
            'name': '__GLOBAL_SETTING__',
            'channels': channels,
            'slackbot_api_token': slackbot_api_token,
            'user_keys': user_keys,
        }
        self.config_collection.update({
            'module':'__GLOBAL__',
            'name':'__GLOBAL_SETTING__'
        }, global_setting, upsert=True)

    def getSlackbotAPIToken(self):
        conf = self.config_collection.find_one({'module':'__GLOBAL__', 'name':'__GLOBAL_SETTING__'})
        if conf:
            return conf['slackbot_api_token']
        else:
            return None

    def getSlackChannels(self):
        conf = self.config_collection.find_one({'module':'__GLOBAL__', 'name':'__GLOBAL_SETTING__'})
        if conf:
            return conf['channels']
        else:
            return None

    def getUserKeys(self, name):
        conf = self.config_collection.find_one({'module':'__GLOBAL__', 'name':'__GLOBAL_SETTING__'})
        if conf:
            return [x for x in conf['user_keys'] if x['module'] == name]
        else:
            return None

    def setSlackChannels(self, channels):
        if type(channels) != list:
            return None
        return self.config_collection.find_one_and_update({'module':'__GLOBAL__', 'name':'__GLOBAL_SETTING__'}, {'$set': {'channels': channels}})

    # Control Config
    def initModule(self, name, default_config):
        if self.validateModule(default_config):
            self.config_collection.update({
                'module':name,
                'name':'__DEFAULT_SETTING__'
            }, default_config, upsert=True)
        else:
            raise Exception('Default config is not valid.')

    def getDefaultConfig(self, name):
        return self.config_collection.find_one({'module':name, 'name':'__DEFAULT_SETTING__'})

    def enable(self, name):
        return self.config_collection.find_one_and_update({'module':name, 'name':'__DEFAULT_SETTING__'}, {'$set': {'__MOD_ENABLE__': True}})

    def disable(self, name):
        return self.config_collection.find_one_and_update({'module':name, 'name':'__DEFAULT_SETTING__'}, {'$set': {'__MOD_ENABLE__': False}})

    def isEnable(self, name):
        data = self.config_collection.find_one({'module':name, 'name':'__DEFAULT_SETTING__'})
        if data and data['__MOD_ENABLE__'] == True:
            return True
        else:
            return False

    def getSafetyCount(self, name):
        data = self.config_collection.find_one({'module':name, 'name':'__DEFAULT_SETTING__'})
        if data:
            return data['__SAFETY__']
        else:
            return -1

    def setSafetyCount(self, name, count):
        updatedata = self.config_collection.find_one({'module':name, 'name':'__DEFAULT_SETTING__'})
        if updatedata:
            updatedata['__SAFETY__'] = count
            self.config_collection.update({
                'module':name,
                'name':'__DEFAULT_SETTING__'
            }, updatedata)
        else:
            raise Exception('Module not Found.')

    def addNewQuery(self, name, query, query_name=None):
        default_query = self.config_collection.find_one({'module':name, 'name':'__DEFAULT_SETTING__'})
        if default_query:
            if 'module_description' in default_query.keys():
                del default_query['module_description']
            insertdata = default_query
            insertdata['query'] = query
            if query_name == None or query_name == '':
                query_name = query
            if self.config_collection.find_one({'module':name, 'name':query_name}):
                raise Exception('Query name collision.')
            insertdata['name'] = query_name
            del insertdata['_id'], insertdata['__SAFETY__'], insertdata['__MOD_ENABLE__']
            for param in insertdata['params']:
                if 'description' in param.keys():
                    del param['description']
                if 'choices' in param.keys():
                    del param['choices']
            if type(insertdata['expire_date']) == int:
                expire_date = datetime.date.today() + datetime.timedelta(days=insertdata['expire_date'])
                insertdata['expire_date'] = expire_date.strftime('%Y-%m-%d')
            replacedata = self.config_collection.find_one({'module':name, 'name':insertdata['name']})
            if not replacedata:
                index = self.config_collection.find({'module':name}).sort('index', -1)[0]['index'] + 1
                insertdata['index'] = index
                self.config_collection.insert(insertdata)
            else:
                index = replacedata['index']
                insertdata['index'] = index
                self.config_collection.update({
                    'module':name,
                    'name':insertdata['name']
                }, insertdata)
            return index
        else:
            raise Exception('Module not Found.')

    def updateConfig(self, name, config):
        default = self.config_collection.find_one({'module':name, 'name':'__DEFAULT_SETTING__'})
        if default == None:
            raise Exception('Module not Found.')
        index = None
        base_query = None
        if 'index' in config.keys():
            data = self.config_collection.find_one({'module':name, 'index':int(config['index'])})
            if data:
                base_query = data
                index = data['index']
        if base_query == None:
            raise Exception('Query not Found.')
        if 'query' in config.keys() and config['query'] != base_query['query'] and config['query'] != '':
            self.setQuery(name, index, config['query'])
        if 'name' in config.keys() and config['name'] != base_query['name'] and config['query'] != '':
            self.setQueryName(name, index, config['name'])
        if 'enable' in config.keys() and str(config['enable']).lower() != str(base_query['enable']).lower():
            if str(config['enable']).lower() == 'true':
                self.enableQuery(name, index)
            elif str(config['enable']).lower() == 'false':
                self.disableQuery(name, index)
        if 'params' in config.keys():
            base_params = base_query['params']
            update_params = config['params']
            for param in default['params']:
                param_name = param['name']
                base_value = [x['value'] for x in base_params if x['name'] == param_name]
                update_value = [x['value'] for x in update_params if x['name'] == param_name]
                if len(update_value) > 0 and (len(base_value) == 0 or base_value[0] != update_value[0]):
                    self.setQueryParam(name, index, param_name, update_value[0])
        if 'channel' in config.keys() and config['channel'] != base_query['channel']:
            self.setChannel(name, index, config['channel'])
        if 'expire_date' in config.keys() and config['expire_date'] != '' and config['expire_date'] != base_query['expire_date']:
            self.setExpireDate(name, index, config['expire_date'])
        if 'filters' in config.keys() and set([x['filter'] for x in config['filters']]) != set([x['filter'] for x in base_query['filters']]):
            self.clearFilters(name, index)
            self.addFilters(name, index, config['filters'])

    def getQueries(self, name):
        return list(self.config_collection.find({'$and': [{'module': name}, {'name': {'$ne': '__DEFAULT_SETTING__'}}]}).sort('Index'))

    def getEnableQueries(self, name):
        return list(self.config_collection.find({'$and': [{'module': name}, {'enable': True}, {'name': {'$ne': '__DEFAULT_SETTING__'}}]}).sort('Index'))

    def getQuery(self, name, index):
        return self.config_collection.find_one({'module':name, 'index':index})

    def getQueryFromName(self, name, query_name):
        return self.config_collection.find_one({'module':name, 'name':query_name})

    def removeQuery(self, name, index):
        return self.config_collection.find_one_and_delete({'module':name, 'index':index})

    def setQuery(self, name, index, query):
        return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$set': {'query': query}})

    def setQueryName(self, name, index, query_name):
        if self.config_collection.find_one({'module':name, 'name':query_name}):
            raise Exception('Query name collision.')
        return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$set': {'name': query_name}})

    def enableQuery(self, name, index):
        return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$set': {'enable': True}})

    def disableQuery(self, name, index):
        return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$set': {'enable': False}})

    def setQueryParam(self, name, index, param_name, param_value):
        default = self.config_collection.find_one({'module':name, 'name':'__DEFAULT_SETTING__'})
        if default == None:
            raise Exception('Module not Found.')
        data = self.config_collection.find_one({'module':name, 'index':index})
        if data:
            param = [x for x in default['params'] if x['name'] == param_name or ('alias' in x.keys() and x['alias'] == param_name)]
            if len(param) == 0:
                data['__update_error'] = 'Parameter not Found.'
                return data
            else:
                param = param[0]
            if 'choices' in param.keys() and not param_value in param['choices']:
                data['__update_error'] = 'Parameter Value is invalid.'
                return data
            data_params = data['params']
            matched = False
            for p in data_params:
                if p['name'] == param['name']:
                    param['value'] = param_value
                    matched = True
                    break
            if not matched:
                param['value'] = param_value
                data_params.append(param)
            self.config_collection.update_one({'module':name, 'index':index}, {'$set': {'params': data_params}})
            return data
        else:
            raise Exception('Query not Found.')

    def setChannel(self, name, index, channel):
        return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$set': {'channel': channel}})

    def setExpireDate(self, name, index, expire_date):
        return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$set': {'expire_date': expire_date}})

    def addFilters(self, name, index, filters):
        data = self.config_collection.find_one({'module':name, 'index':index})
        if data:
            current_filters = data['filters']
            if len(current_filters) == 0:
                current_id = 1
            else:
                current_id = max([x['id'] for x in current_filters]) + 1
            new_filters = []
            for f in filters:
                new_filters.append({'id':current_id, 'filter':f['filter']})
                current_id += 1
            return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$push': {'filters':{'$each': new_filters}}})
        else:
            return None

    def clearFilters(self, name, index):
        return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$set': {'filters': []}})

    def setExcludeList(self, name, index, exclude_list):
        if len(exclude_list) != 0:
            return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$set': {'exclude_list': exclude_list}})
        else:
            return None

    def firstRunIsFinished(self, name, index):
        return self.config_collection.find_one_and_update({'module':name, 'index':index}, {'$set': {'__INITIAL__': False}})

    # Control Results
    def setResult(self, result):
        self.result_collection.insert(result)

    def getResult(self, name, query='all', limit=10, page=0, sort=None, empty='true', status='all'):
        skip = limit * page
        if not sort:
            sort = 'module_start'
        q = {'$and': [{'module': name}]}
        if query != 'all':
            q['$and'].append({'query_name': query})
        if empty != 'true':
            q['$and'].append({'result_count': {'$ne': 0}})
        if status != 'all':
            q['$and'].append({'status.status': status})
        return self.result_collection.find(q).sort(sort, -1).skip(skip).limit(limit), self.result_collection.count_documents(q)

    # Control Jobs
    def initJob(self, jobs):
        self.job_collection.remove({})
        for job_name, job_schedule in jobs:
            next_time = datetime.datetime.now() + datetime.timedelta(seconds=math.ceil(CronTab(job_schedule).next()))
            insertdata = {
                'module': job_name,
                'enable': True,
                'last_run': None,
                'next_run': next_time,
                'process_id': -1,
                'status': 'Waiting',
                'schedule': job_schedule
            }
            self.job_collection.insert(insertdata)

    def runNow(self, name):
        now = datetime.datetime.now()
        data = self.job_collection.find_one_and_update({'module':name}, {'$set': {'next_run': now}})

    def setCronSchedule(self, name, crontab):
        data = self.job_collection.find_one_and_update({'module':name}, {'$set': {'schedule': crontab}})

    def startJob(self, name, process_id):
        now = datetime.datetime.now()
        updatedata = {
            'last_run': now,
            'process_id': process_id,
            'status': 'Ruuning',
        }
        data = self.job_collection.find_one_and_update({'module':name, 'status':'Waiting'}, {'$set': updatedata})

    def finishJob(self, name, extra=None):
        now = datetime.datetime.now()
        data = self.job_collection.find_one({'module':name})
        if data:
            schedule = data['schedule']
            next_time = datetime.datetime.now() + datetime.timedelta(seconds=math.ceil(CronTab(schedule).next()))
            if extra != None:
                next_time += datetime.timedelta(day=extra['days'], hour=extra['hours'], mitute=extra['minutes'], seconds=extra['seconds'])
            updatedata = {
                'enable': True,
                'next_run': next_time,
                'process_id': -1,
                'status': 'Waiting',
            }
            self.job_collection.update({'module':name}, {'$set': updatedata})

    def getJob(self, name):
        return self.job_collection.find_one({'module':name})

    def getRunJob(self):
        now = datetime.datetime.now()
        return self.job_collection.find_one({'$and': [{'next_run': {'$lte': now}}, {'status': 'Waiting'}, {'enable': True}]})
