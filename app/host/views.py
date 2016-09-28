# coding: utf-8
from flask import abort, render_template, redirect, request, jsonify
from . import host
from ..models import EventLog, HostList, EventList, SysInfoLog, PostLog
import json

@host.route('/hostlist')
def hostlist():
    hosts = HostList.query
    hostList = []
    for host in hosts:
        sys_ok_cnt = 0
        sys_warning_cnt = 0
        sys_error_cnt = 0
        event_ok_cnt = 0
        event_warning_cnt = 0
        event_error_cnt = 0
        event_unknown_cnt = 0
        items = ['cpu', 'memory', 'disk', 'service', 'database']
        for item in items:
            itemInfo = SysInfoLog.getItemInfo(host.host, item)
            if itemInfo is not None and len(itemInfo) > 0:
                if itemInfo.startswith('error'):
                    sys_error_cnt = sys_error_cnt + 1
                elif itemInfo.startswith('warning'):
                    sys_warning_cnt = sys_error_cnt + 1
                else:
                    sys_ok_cnt = sys_ok_cnt + 1
        eventLists = EventList.getDailyEventList(host.host)

        event_ok_cnt = EventLog.getOkCnt(host.host)
        event_warning_cnt = EventLog.getWarningCnt(host.host)
        event_error_cnt = EventLog.getErrorCnt(host.host)
        event_unknown_cnt = EventLog.getUnknownCnt(host.host)

        data = {
            'host': host.host,
            'name': host.name,
            'sys_ok_cnt': sys_ok_cnt,
            'sys_error_cnt': sys_error_cnt,
            'sys_warning_cnt': sys_warning_cnt,
            'event_ok_cnt': event_ok_cnt,
            'event_error_cnt': event_error_cnt,
            'event_warning_cnt': event_warning_cnt,
            'event_unknown_cnt': event_unknown_cnt
        }
        hostList.append(data)

    return render_template('host/hostlist.html', HostList=hostList)

@host.route('/hostdetail')
def hostdetail():
    host = request.args.get('host')
    hostName = ''
    if host is None:
        return redirect('host/hostlist')
    else:
        hostName = HostList.getHostInfo(host).name

    date_time = ''
    sysinfoList=[]
    items=['cpu', 'memory', 'disk', 'service', 'database']
    itemsname = {'cpu':u'CPU', 'memory':u'内存', 'disk':u'磁盘', 'service':u'服务', 'database':u'数据库'}
    sysDateTime = SysInfoLog.getItemInfo(host, 'date_time')
    for item in items:
        itemInfo = SysInfoLog.getItemInfo(host, item)
        info = []
        status = ''
        if itemInfo is not None:
            ia = itemInfo.split('|')
            for ii in ia:
                s = ''
                if (ii.startswith('error')):
                    s = 'error'
                    status = 'error'
                    ii = ii[len(s)+1:len(ii)-1]
                elif (ii.startswith('warning')):
                    s = 'warning'
                    if status != 'error':
                        status = 'warning'
                    ii = ii[len(s) + 1:len(ii) - 1]

                info.append({'info':ii, 'status':s})

        data={
            'item': itemsname[item],
            'info': info,
            'status': status
        }
        sysinfoList.append(data)

    eventList = []
    eventLists = EventList.getDailyEventList(host)
    for list in eventLists:
        date_time = ''
        last = EventLog.getLast(host, list.event)
        if last is not None:
            date_time = last.operation_datetime

        data={
            'event': list.event,
            'name': list.name,
            'date_time': date_time,
            'ok_cnt': EventLog.getOkCnt(host, list.event),
            'error_cnt': EventLog.getErrorCnt(host, list.event),
            'warning_cnt': EventLog.getWarningCnt(host, list.event),
            'unknown_cnt': EventLog.getUnknownCnt(host, list.event)
        }
        eventList.append(data)

    request_event = request.args.get('event')
    eventName = ''
    eventLogs=[]
    if request_event is not None:
        event_log = EventLog.query.filter_by(host=host, event=request_event, operation_type='root').order_by(EventLog.event_datetime.desc())
        for log in event_log:
            operation = log.operation
            sysinfo_id = log.sysinfo_id
            status = ''
            if operation is not None:
                if operation.startswith('error'):
                    status = 'error'
                elif operation.startswith('warning'):
                    status = 'warning'
                else:
                    status = 'ok'
            status = log.status
            if status is None:
                status = ''
            if sysinfo_id is None:
                sysinfo_id = 0
            data = {
                'id': log.id,
                'event_id': log.event_id,
                'status': status,
                'event_datetime': log.event_datetime,
                'content': log.content,
                'operation': operation,
                'operation_datetime': log.operation_datetime,
                'sysinfo_id': sysinfo_id
            }
            eventLogs.append(data)
        eventName = EventList.query.filter_by(event=request_event).first().name
    else:
        eventLogs = None
    return render_template('host/hostdetail.html', EventList=eventList, EventLogs=eventLogs, Host=host, HostName=hostName, EventName=eventName, SysInfoList=sysinfoList, SysDateTime=sysDateTime)

@host.route('/postlog', methods=['GET', 'POST'])
def postlog():
    try:
        if not request.values or not 'event_log' in request.values or not 'sysinfo_log' in request.values or not 'host' in request.values:
            return 'error'

        request_sysinfo_log = json.loads(request.values['sysinfo_log'])
        host = request.values['host']
        if HostList.getHostInfo(host) is None:
           return 'error(host info not in option)'

        sysinfo_operation = ''
        sysinfo_host = host
        sysinfo_sys_date = ''
        sysinfo_sys_time = ''
        sysinfo_cpu = ''
        sysinfo_memory = ''
        sysinfo_disk = ''
        sysinfo_service = ''
        sysinfo_database = ''
        sysinfo_error=[]
        sysinfo_warning = []

        if request_sysinfo_log.get('sys_date') is None:
            sysinfo_sys_date = 'error(no sys_date)'
        else:
            sysinfo_sys_date = request_sysinfo_log.get('sys_date')

        if request_sysinfo_log.get('sys_time') is None:
            sysinfo_sys_time = 'error(no sys_time)'
        else:
            sysinfo_sys_time = request_sysinfo_log.get('sys_time')

        if request_sysinfo_log.get('cpu') is None:
            sysinfo_cpu = 'error(cpu)'
        elif request_sysinfo_log.get('cpu') > HostList.getHostInfo(sysinfo_host).max_cpu:
            sysinfo_cpu = 'warning(overload cpu :{0}'.format(request_sysinfo_log.get('cpu'))
        else:
            sysinfo_cpu = request_sysinfo_log.get('cpu')

        if request_sysinfo_log.get('memory') is None:
            sysinfo_memory = 'error(no memory)'
        elif request_sysinfo_log.get('memory') > HostList.getHostInfo(sysinfo_host).max_memory:
            sysinfo_memory = 'warning(overload memory : {0})'.format(request_sysinfo_log.get('memory'))
        else:
            sysinfo_memory = request_sysinfo_log.get('memory')

        if request_sysinfo_log.get('disk') is None:
            sysinfo_disk = 'error(no disk)'
        elif len(request_sysinfo_log.get('disk')) > 0:
            for info in request_sysinfo_log.get('disk'):
                if info.get('used') > HostList.getHostInfo(sysinfo_host).max_disk:
                    sysinfo_disk += 'warning(overload disk : {0} : {1})|'.info.get('partion'), format(info.get('used'))
                else:
                    sysinfo_disk += '{0} : {1}|'.format(info.get('partion'), info.get('used'))
            if (sysinfo_disk.endswith('|')):
                sysinfo_disk = sysinfo_disk[:len(sysinfo_disk)-1]

        if request_sysinfo_log.get('service') is None:
            sysinfo_service = 'error(no service)'
        else:
            for info in request_sysinfo_log.get('service'):
                cpu = 'cpu : {0}'.format(info.get('cpu'))
                create_time = 'create_time : {0}'.format(info.get('create_time'))
                pid = 'pid : {0}'.format(info.get('pid'))
                name = 'name : {0}'.format(info.get('name'))
                memory = 'memory : {0}'.format(info.get('memory'))
                sysinfo_service += '{0},{1},{2},{3},{4}|'.format(cpu, create_time, pid, name, memory)
            if (sysinfo_service.endswith('|')):
                sysinfo_service = sysinfo_service[:len(sysinfo_service)-1]

        if request_sysinfo_log.get('database') is None:
            sysinfo_database = 'error(no database)'
        elif len(request_sysinfo_log.get('database')) == 0:
            sysinfo_database = 'error(no instance in database)'
        else:
            for info in request_sysinfo_log.get('database'):
                dbtype = info.get('dbtype')
                cnn_cnt = info.get('cnn_cnt')
                dbname = info.get('dbname')
                dbinfo = '{0} : {1} : {2}'.format(cnn_cnt, dbtype , dbname)

                if cnn_cnt is None or len(str(cnn_cnt)) == 0:
                    sysinfo_database += 'error(can not be connected : ' + dbinfo + ')|'
                if (dbtype == 'postgres' and cnn_cnt > HostList.getHostInfo(sysinfo_host).max_postgres) or \
                    (dbtype == 'mysql' and cnn_cnt > HostList.getHostInfo(sysinfo_host).max_mysql):
                    sysinfo_database += 'warning(overload connection : ' + dbinfo + ')|'
                else:
                    sysinfo_database += dbinfo + '|'
            if (sysinfo_database.endswith('|')):
                sysinfo_database = sysinfo_database[:len(sysinfo_database) - 1]

        sysinfo_log = {
            'host': sysinfo_host,
            'sys_date': sysinfo_sys_date,
            'sys_time': sysinfo_sys_time,
            'cpu': sysinfo_cpu,
            'memory': sysinfo_memory,
            'disk': sysinfo_disk,
            'service': sysinfo_service,
            'database': sysinfo_database
        }
        sysinfo_id = SysInfoLog.insertSysInfoLog(sysinfo_log)

        event_logs=[]
        request_event_log = json.loads(request.values['event_log'])
        if not len(request_event_log) == 0:
            for log in request_event_log:
                status = log.get('status')
                event_datetime = '{0} {1}'.format(log.get('event_date'), log.get('event_time'))
                eventList = EventList.query.filter_by(scheduled_type='day', event=log.get('event')).first()
                operation = 'unknown'
                if status == u'executing':
                    operation='ok(executing)'
                    if eventList.scheduled_start_time < log['event_time']:
                        operation ='warning(start delay)'
                elif status == u'done':
                    operation = 'ok(done)'
                    if eventList.scheduled_end_time < log['event_time']:
                        operation ='warning(end delay)'
                elif status == u'error':
                    operation = 'error(custom error)'
                event_log = {
                    'host': host,
                    'event_id': log['event_id'],
                    'event_datetime': event_datetime,
                    'event': log['event'],
                    'status': status,
                    'content': log['content'],
                    'operation': operation,
                    'operation_type': 'root',
                    'sysinfo_id': sysinfo_id
                }
                EventLog.insertEventLog(event_log)
        PostLog.insertPostLog(str(request.values), '')
    except Exception as ex:
        PostLog.insertPostLog(str(request.values), str(ex))
        return str(ex)

    return 'ok'

@host.route('/operation/detail')
def operationdetail():
    status = request.args.get('status')
    if status is None:
        sysinfo = []
        items = ['cpu', 'memory', 'disk', 'service', 'database']
        itemsname = {'cpu': u'CPU', 'memory': u'内存', 'disk': u'磁盘', 'service': u'服务', 'database': u'数据库'}
        sysinfo_id = request.args.get('sysinfo_id')
        for item in items:
            itemInfo = SysInfoLog.getItemInfo(host, item, sysinfo_id)
            info = []
            istatus = ''
            if itemInfo is not None:
                ia = itemInfo.split('|')
                for ii in ia:
                    s = ''
                    if (ii.startswith('error')):
                        s = 'error'
                        istatus = 'error'
                        ii = ii[len(s) + 1:len(ii) - 1]
                    elif (ii.startswith('warning')):
                        s = 'warning'
                        if istatus != 'error':
                            istatus = 'warning'
                        ii = ii[len(s) + 1:len(ii) - 1]

                    info.append({'info': ii, 'status': s})

            data = {
                'item': itemsname[item],
                'info': info,
                'status': istatus
            }
            sysinfo.append(data)

        return jsonify({'sysinfo': sysinfo})
    else:
        log_id = request.args.get('log_id')
        comment = request.args.get('comment')
        operation = EventLog.getOperationById(log_id)
        if not operation is None and operation != '':
            operation = status + '-' + operation
        else:
            operation = status

        event_log = EventLog.updateOperationById(log_id, operation)

        log = {
            'host': event_log.host,
            'event_id': event_log.event_id,
            'event_datetime': event_log.event_datetime,
            'event': event_log.event,
            'status': status,
            'content': comment,
            'operation': log_id,
            'operation_type': 'branch',
            'sysinfo_id': ''
        }
        EventLog.insertEventLog(log)

        return jsonify({'result': 'ok'})

@host.route('/operation/history')
def operationhistory():
    event_id = request.args.get('event_id')
    log_id = request.args.get('log_id')
    event_log = EventLog.getOperationHistoryByEventId(event_id, log_id)
    history = []
    for log in event_log:
        status = ''
        if log.status == 'fix':
            status = u'修复'
        elif log.status == 'ignor':
            status = u'忽略'
        elif log.status == 'error':
            status = u'错误'
        data = {
            'status': status,
            'date_time': log.operation_datetime,
            'comment': log.content
        }
        history.append(data)

    return jsonify({'result': 'ok', 'history': history})