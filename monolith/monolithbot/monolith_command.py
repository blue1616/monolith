from slackbot.bot import respond_to
from slackbot.bot import listen_to

import sys

sys.path.append('../util')
from util.dbHelper import Helper

db = None

def setDB(BD_HOST, DB_PORT, DB_NAME):
    global db
    db = Helper(BD_HOST, DB_PORT, DB_NAME)

def paramParser(params, args_list):
    parsedparam = {}
    tmp = ''
    ordered_value = []
    is_string = False
    param_name = ''
    param_value = ''
    pointer = 0
    while pointer < len(params):
        c = params[pointer]
        if c == ' ' or c == ';':
            if is_string:
                tmp += c
            elif tmp != '':
                if param_name != '':
                    parsedparam[param_name] = tmp
                    args_list.remove(param_name)
                else:
                    ordered_value.append(tmp)
                tmp = ''
                is_string = False
                param_name = ''
                param_value = ''
        elif c == '"':
            if is_string:
                if param_name != '':
                    parsedparam[param_name] = tmp
                    args_list.remove(param_name)
                else:
                    ordered_value.append(tmp)
                tmp = ''
                is_string = False
                param_name = ''
                param_value = ''
            else:
                is_string = True
        elif c == '=':
            if is_string:
                tmp += c
            else:
                if tmp in args_list:
                    param_name = tmp
                    tmp = ''
                else:
                    tmp += c
        elif c == '\\':
            if pointer + 1 < len(params) and params[pointer+1] in [' ',';','"','=','\\']:
                tmp += params[pointer+1]
                pointer += 1
            else:
                tmp += c
        else:
            tmp += c
        pointer += 1
    if tmp != '':
        if param_name != '':
            parsedparam[param_name] = tmp
        else:
            ordered_value.append(tmp)
    for p in ordered_value:
        p_name = args_list.pop(0)
        parsedparam[p_name] = p
        if len(args_list) <= 0:
            break
    return parsedparam

def replay(message, post_data):
    message._client.webapi.chat.post_message(
        message._body['channel'],
        post_data,
        as_user=True,
    )

@respond_to('disableModule:(.*)')
def disableModule(message, params):
    post_data = ''
    requires = ['module']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if db.disable(args['module']):
                post_data = 'Module {name} is disabled.'.format(name=args['module'])
            else:
                post_data = 'Error: Something Wrong...'
        else:
            post_data = 'Error: Module not found.'
    else:
        post_data = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('enableModule:(.*)')
def enableModule(message, params):
    post_data = ''
    requires = ['module']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if db.enable(args['module']):
                post_data = 'Module {name} is enabled.'.format(name=args['module'])
            else:
                post_data = 'Error: Something Wrong...'
        else:
            post_data = 'Error: Module not found.'
    else:
        post_data = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('setQuery:(.*)')
@respond_to('setQ:(.*)')
@respond_to('setKeyword:(.*)')
@respond_to('setK:(.*)')
def setQuery(message, params):
    post_data = ''
    requires = ['module', 'query']
    optional = ['name', 'enable', 'expire_date', 'channel']
    args = paramParser(params, requires+optional)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if args['query'] == '':
                post_data = 'Error: Query is Empty.'
            else:
                query_name = None
                if 'name' in args.keys():
                    query_name = args['name']
                query_id = db.addNewQuery(args['module'], args['query'], query_name)
                opt = {}
                if 'enable' in args.keys():
                    opt['enable'] = args['enable']
                if 'expire_date' in args.keys():
                    opt['expire_date'] = args['expire_date']
                if 'channel' in args.keys():
                    opt['channel'] = args['channel']
                if opt != {}:
                    opt['index'] = query_id
                    db.updateConfig(name=args['module'], config=opt)
                post_data = 'Query `{query}` is successfully registered(index: {query_id}).'.format(query=args['query'], query_id=query_id)
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('removeQuery:(.*)')
@respond_to('removeQ:(.*)')
@respond_to('removeKeyword:(.*)')
@respond_to('removeK:(.*)')
def removeQuery(message, params):
    post_data = ''
    requires = ['module', 'query']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if args['query'] == '':
                post_data = 'Error: Query is Empty.'
            elif not args['query'].isdigit():
                post_data = 'Error: Invalid Query Index.'
            else:
                removed = db.removeQuery(args['module'], int(args['query']))
                if removed:
                    post_data = 'Query `{name}` ({id}) was removed.'.format(name=removed['name'], id=removed['index'])
                else:
                    post_data = 'Error: Query not Found'
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('disableQuery:(.*)')
@respond_to('disableQ:(.*)')
@respond_to('disableKeyword:(.*)')
@respond_to('disableK:(.*)')
def disableQuery(message, params):
    post_data = ''
    requires = ['module', 'query']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if args['query'] == '':
                post_data = 'Error: Query is Empty.'
            elif not args['query'].isdigit():
                post_data = 'Error: Invalid Query Index.'
            else:
                disabled = db.disableQuery(args['module'], int(args['query']))
                if disabled:
                    post_data = 'Query `{name}` ({id}) was disabled.'.format(name=disabled['name'], id=disabled['index'])
                else:
                    post_data = 'Error: Query not Found'
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('enableQuery:(.*)')
@respond_to('enableQ:(.*)')
@respond_to('enableKeyword:(.*)')
@respond_to('enableK:(.*)')
def enableQuery(message, params):
    post_data = ''
    requires = ['module', 'query']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if args['query'] == '':
                post_data = 'Error: Query is Empty.'
            elif not args['query'].isdigit():
                post_data = 'Error: Invalid Query Index.'
            else:
                enabled = db.enableQuery(args['module'], int(args['query']))
                if enabled:
                    post_data = 'Query `{name}` ({id}) was enabled.'.format(name=enabled['name'], id=enabled['index'])
                else:
                    post_data = 'Error: Query not Found'
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('setParam:(.*)')
@respond_to('setP:(.*)')
def setParam(message, params):
    post_data = ''
    requires = ['module', 'query', 'param_name', 'param_value']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if args['query'] == '':
                post_data = 'Error: Query is Empty.'
            elif not args['query'].isdigit():
                post_data = 'Error: Invalid Query Index.'
            else:
                updated = db.setQueryParam(args['module'], int(args['query']), args['param_name'], args['param_value'])
                if not updated:
                    post_data = 'Error: Query not Found'
                elif not '__update_error' in updated.keys():
                    post_data = 'Param: {param_name}  of Query `{name}` ({id}) changed to {param_value}.'.format(name=updated['name'], id=updated['index'], param_name=args['param_name'], param_value=args['param_value'])
                else:
                    post_data = 'Error: ' + updated['__update_error']
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('setExpireDate:(.*)')
@respond_to('setED:(.*)')
def setExpireDate(message, params):
    post_data = ''
    requires = ['module', 'query', 'expire_date']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if args['query'] == '':
                post_data = 'Error: Query is Empty.'
            elif not args['query'].isdigit():
                post_data = 'Error: Invalid Query Index.'
            else:
                updated = db.setExpireDate(args['module'], int(args['query']), args['expire_date'])
                if updated:
                    post_data = 'Expire Date of `{name}` ({id}) is {expire_date}.'.format(name=updated['name'], id=updated['index'], expire_date=args['expire_date'])
                else:
                    post_data = 'Error: Query not Found'
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('setChannel:(.*)')
@respond_to('setC:(.*)')
def setChannel(message, params):
    post_data = ''
    requires = ['module', 'query', 'channel']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if args['query'] == '':
                post_data = 'Error: Query is Empty.'
            elif not args['query'].isdigit():
                post_data = 'Error: Invalid Query Index.'
            else:
                updated = db.setChannel(args['module'], int(args['query']), args['channel'])
                if updated:
                    if args['channel'] in db.getSlackChannels():
                        post_data = 'Results of `{name}` ({id}) notifiy to #{channel}.'.format(name=updated['name'], id=updated['index'], channel=args['channel'])
                    else:
                        post_data = 'Results of `{name}` ({id}) doesn\'t notify.'.format(name=updated['name'], id=updated['index'])
                else:
                    post_data = 'Error: Query not Found'
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('addFilter:(.*)')
@respond_to('addF:(.*)')
def addFilter(message, params):
    post_data = ''
    requires = ['module', 'query', 'filter']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if args['query'] == '':
                post_data = 'Error: Query is Empty.'
            elif not args['query'].isdigit():
                post_data = 'Error: Invalid Query Index.'
            else:
                if 'filter' != '':
                    updated = db.addFilters(args['module'], int(args['query']), [{'filter':args['filter']}])
                    if updated:
                        post_data = 'Filter: {filter} added to `{name}` ({id}).'.format(name=updated['name'], id=updated['index'], filter=args['filter'])
                    else:
                        post_data = 'Error: Query not Found'
                else:
                    post_data = 'Error: Filter is Empty.'
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('getQueries:(.*)')
@respond_to('getQ:(.*)')
@respond_to('getKeyword:(.*)')
@respond_to('getK:(.*)')
def getQueries(message, params):
    post_data = ''
    requires = ['module']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            queries = db.getEnableQueries(args['module'])
            post_data = 'Enabled Query list of {}.\n```'.format(args['module'])
            for q in queries:
                post_data += '{id}: `{name}` : {query}'.format(id=q['index'], name=q['name'], query=q['query'])
            post_data += '```'
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('getAllQueries:(.*)')
@respond_to('getAllQ:(.*)')
@respond_to('getAllKeyword:(.*)')
@respond_to('getAllK:(.*)')
def getAllQueries(message, params):
    post_data = ''
    requires = ['module']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            queries = db.getQueries(args['module'])
            post_data = 'Enabled Query list of {}.\n```'.format(args['module'])
            for q in queries:
                post_data += '{id}: {name} : {query}\n'.format(id=q['index'], name=q['name'], query=q['query'])
            post_data += '```'
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('getSettings:(.*)')
@respond_to('getS:(.*)')
def getSettings(message, params):
    post_data = ''
    requires = ['module', 'query']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        if args['module'] in db.getModuleName():
            if args['query'].isdigit():
                query = db.getQuery(args['module'], int(args['query']))
            else:
                query = db.getQueryFromName(args['module'], args['query'])
            if query:
                post_data = 'Settings of Query: `{name}`.\n```'.format(name=query['name'])
                param_view = [
                    'index',
                    'name',
                    'query',
                    'params',
                    'expire_date',
                    'channel',
                    'filters',
                ]
                for p in param_view:
                    param = p.upper().replace('_', ' ')
                    if p == 'filters':
                        value = ', '.join([x['filter'] for x in query[p]])
                    elif p == 'params':
                        value = '\n\t'
                        value += '\n\t'.join([x['name']+': '+x['value'] for x in query[p]])
                    else:
                        value = query[p]
                    post_data += '{key}: {value}\n'.format(key=param, value=value)
                post_data += '```'
            else:
                post_data = 'Error: Query `{name}` not found.'.format(name=args['query'])
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('getJobState:(.*)')
@respond_to('getJS:(.*)')
def getJobState(message, params):
    post_data = ''
    requires = ['module']
    args = paramParser(params, requires)
    if len([True for x in requires if x in args.keys()]) == len(requires):
        job = db.getJob(args['module'])
        if job:
            param_view = [
                'enable',
                'last_run',
                'next_run',
                'schedule',
            ]
            post_data = 'Job State of Module: `{name}`.\n```'.format(name=args['module'])
            for p in param_view:
                post_data += '{key}: {value}\n'.format(key=p, value=str(job[p]))
            post_data += '```'
        else:
            post_data = 'Error: Module not found.'
    else:
        message = 'Error: Parameter Shortage.'
    if post_data != '':
        replay(message, post_data)

@respond_to('help:')
def getHelp(message):
    help_message = '''```Command List:
\'enableModule: {module}\'\tDisable module.
\'disableModule: {module}\'\tDisable module.
\'setQuery: {module}; {query};\'\tAdd [query] as New Search query with Default Settings. And, able to continue to specify query parameters(name, enable, expire_date, channel) as an optional argument
 (abbreviation=setQ:)
\'setQuery: {module}; {query};\'\tAdd [query] as New Search query with Default Settings. And, able to continue to specify query parameters(name, enable, expire_date, channel) as an optional argument
 (abbreviation=setQ:)
\'removeQuery: {module}; {query}\'tRemove the Search query indicated by query index.
 (abbreviation=removeQ:)
\'enableQuery: {module}; {query}\'\tEnable the Search query indicated by query index.
 (abbreviation=enableQ:)
\'disableQuery: {module}; {query}\'\tDisable the Search query indicated by query index.
 (abbreviation=disableQ:)
\'setParam: {module}; {query}; {param_name}; {param_value}\'\tSet Parameter of Search Query indicated by query index.
 (abbreviation=setP:)
\'setExpireDate: {module}; {query}; {expiration_date}\'\tSet a Expiration Date of Search Query indicated by [index].
 (abbreviation=setED:)
\'setChannel: {module}; {query}; {channel}\'\tSet channel to notify the Search Query\'s result.
 (abbreviation=setC:)
\'addFilter: {module}; {query}; {filter}\'\tAdd new Result Filter.
 (abbreviation=setF:)
\'getQueries: {module};\'\tListing Enabled Search Keywords.
 (abbreviation=getQ:)
\'getAllQueries: {module};\'\tListing Enabled Search Keywords.
 (abbreviation=getAllQ:)
\'getSettings: {module}; {query};\'\tShow Setting of the Search Keyword indicated by query index.
 (abbreviation=getS:)

\'help:\'\tShow this Message.
\n```'''
    message._client.webapi.chat.post_message(
        message._body['channel'],
        help_message,
        as_user=True,
    )

@listen_to('How are you?')
def reaction(message):
    isername=message._client.login_data['self']['name'],
    message.send('I\'m fine.')
