from util.dbHelper import Helper
from util.scheduleJob import JobConfig
from util.slack_post import postData

import argparse
from crontab import CronTab
import datetime
import dateutil.parser
from importlib import import_module
import logging
from monolithbot import monolith_command
from multiprocessing import Pool
import os
from slackbot.bot import Bot
import slackbot_settings
import sys
import time
import traceback

BD_HOST = ''
DB_PORT = 0
DB_NAME = ''

loaded_modules = {}

def getDateObject(datetime_str):
    try:
        return dateutil.parser.isoparse(datetime_str).date()
    except:
        return None

def runSearch(db):
    now = datetime.datetime.now()
    runningJob = db.getRunJob()
    while runningJob:
        run_target = runningJob['module']
        logging.info(run_target + ' is Running!')
        db.startJob(run_target, os.getpid())
        module = loaded_modules[run_target]
        try:
            module.initModule()
            error_count = db.getSafetyCount(module.name)
            user_keys = db.getUserKeys(module.name)
            empty_key = [x for x in user_keys if x['requred'] and (x['value'] == None or x['value'] == '')]
            if len(empty_key) > 0:
                message = run_target + ' requires API key. Disable Module.'
                logging.info(message)
                postData(db.getSlackbotAPIToken(), message, slackbot_settings.channels[0])
                db.disable(module.name)
            if db.isEnable(module.name):
                module.user_keys = user_keys
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                for query in db.getEnableQueries(module.name):
                    module.run(query, timestamp)
                    result = module.getResult()
                    db.setExcludeList(result['module'], result['query_id'], module.getExcludeList())
                    expire = getDateObject(query['expire_date'])
                    if expire != None and datetime.date.today() >= expire:
                        db.disableQuery(result['module'], result['query_id'])
                        message = 'Query: `{name}`(id:{id}) is Expired. Disable Query.'.format(name=result['module'], id=result['query_id'])
                        postData(db.getSlackbotAPIToken(), message, query['channel'])
                    db.setResult(result)
                    if result['status']['status'] == 'OK':
                        error_count = 0
                    else:
                        error_count += 1
                    if error_count >= module.max_error_count:
                        module.enable_extra_interval = True
                        db.setSafetyCount(module.name, 0)
                        break
                    db.setSafetyCount(module.name, error_count)

                    if module.updateQuery != {}:
                        updateinfo = module.updateQuery
                        updateinfo['index'] = query['index']
                        db.updateConfig(module.name, updateinfo)
                    if not (module.not_notify_at_first_time and query['__INITIAL__']):
                        messages = module.createMessage()
                        if query['channel'] in db.getSlackChannels():
                            message = ''
                            if type(messages) == list and len(messages) > 0:
                                postData(db.getSlackbotAPIToken(), '\n'.join(messages), query['channel'])
                            elif type(messages) == str and len(messages) > 0:
                                postData(db.getSlackbotAPIToken(), messages, query['channel'])
                    if query['__INITIAL__']:
                        db.firstRunIsFinished(result['module'], result['query_id'])
            if module.enable_extra_interval:
                logging.info('Something Occurred and Sleep for a while...')
                message = 'Extra Interval is '
                for k,v in module.extra_interval.items():
                    if v != 0:
                        message += str(v) + k + ' '
                logging.info(message)
                db.finishJob(run_target, module.extra_interval)
            else:
                db.finishJob(run_target)
            logging.info(run_target + ' is finished!')
        except:
            logging.error(traceback.format_exc())
        runningJob = db.getRunJob()

def runBot():
    monolith_command.setDB(BD_HOST, DB_PORT, DB_NAME)
    bot = Bot()
    bot.run()

def job_controller(jobConfig):
    db = Helper(BD_HOST, DB_PORT, DB_NAME)
    while True:
        try:
            time.sleep(jobConfig.next())
            jobConfig.job(db)
        except KeyboardInterrupt:
            break

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-host', type=str, default='localhost', help='DATABASE HOST NAME')
    parser.add_argument('--db-port', type=int, default=27017, help='DATABASE PORT')
    parser.add_argument('--db-name', type=str, default='monolith-database', help='DATABASE NAME')
    args = parser.parse_args()

    global BD_HOST
    global DB_PORT
    global DB_NAME
    BD_HOST = args.db_host
    DB_PORT = args.db_port
    DB_NAME = args.db_name

    db = Helper(BD_HOST, DB_PORT, DB_NAME)
    crontab_interval = '* * * * *'
    process_number = slackbot_settings.process_number

    file_handler = logging.FileHandler(filename='logs/run.log')
    stdout_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(process)d - %(levelname)s - %(name)s - *** %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[file_handler, stdout_handler]
    )

    jobs = []
    user_keys = []
    for mod_name in slackbot_settings.modules:
        mod = import_module('.' + mod_name, 'modules')
        load_module = mod.CustomModule()
        load_module.set()
        for key in load_module.user_keys:
            key['module'] = load_module.name
            if key['name'] in slackbot_settings.user_keys.keys():
                key['value'] = slackbot_settings.user_keys[key['name']]
            user_keys.append(key)
        interval = ''
        if mod_name in slackbot_settings.intervals.keys():
            interval = slackbot_settings.intervals[mod_name]
        else:
            interval = load_module.run_interval
        loaded_modules[load_module.name] = load_module
        db.initModule(load_module.name, load_module.getDefaultQuery())
        jobs.append((load_module.name, interval))
        logging.info('Module: {name} is successfully loaded!'.format(name=load_module.name))

    db.initJob(jobs)
    jobConfigs = [JobConfig(CronTab(crontab_interval), runSearch, (7 * x ) % 60) for x in range(process_number)]

    postdata = '---Monolithbot Started. Loaded Modules are as follows.---\n```'
    postdata += '\n'.join(loaded_modules.keys())
    postdata += '```'
    post_succeeded = postData(slackbot_settings.API_TOKEN, postdata, slackbot_settings.channels[0])
    if post_succeeded:
        db.setGlobalConfig(slackbot_api_token=slackbot_settings.API_TOKEN, channels=slackbot_settings.channels, user_keys=user_keys)
    else:
        logging.error('Slack API is invalid. Disable Slackbot.')
        db.setGlobalConfig(slackbot_api_token='', channels=slackbot_settings.channels, user_keys=user_keys)

    if slackbot_settings.enable_slackbot and post_succeeded:
        process_number = len(jobConfigs) + 1
    else:
        process_number = len(jobConfigs)
    p = Pool(process_number)
    try:
        if slackbot_settings.enable_slackbot and post_succeeded:
            p.apply_async(runBot)
        p.map(job_controller, jobConfigs)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
