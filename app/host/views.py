# coding: utf-8
from flask import abort, render_template, redirect, flash, \
    url_for, request, current_app, jsonify
from . import host
from ..models import EventLog, HostList, EventList, SysInfoLog
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
        for list in eventLists:
            event_ok_cnt = event_ok_cnt + EventLog.getOkCnt(host.host, list.event)
            event_warning_cnt = event_warning_cnt + EventLog.getWarningCnt(host.host, list.event)
            event_error_cnt = event_error_cnt + EventLog.getErrorCnt(host.host, list.event)
            event_unknown_cnt = event_unknown_cnt + EventLog.getUnknownCnt(host.host, list.event)
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
        status = ''
        css = 'badge badge-grey '
        if itemInfo is not None:
            if itemInfo.startswith('error'):
                status = 'error'
                info = itemInfo[len(status)+1:len(itemInfo)-1]
                css = 'badge badge-important '
            elif itemInfo.startswith('warning'):
                status = 'warning'
                info = itemInfo[len(status)+1:len(itemInfo)-1]
                css = 'badge badge-warning '
            else:
                status = 'ok'
                info = itemInfo
                css = 'badge badge-success '

        data={
            'item': itemsname[item],
            'info': info,
            'status': status,
            'css': css
        }
        sysinfoList.append(data)

    eventList = []
    eventLists = EventList.getDailyEventList(host)
    for list in eventLists:
        last = EventLog.getLast(host, list.event)
        if last is not None:
            date_time = last.event_date + ' ' + last.event_time

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
        eventLog = EventLog.query.filter_by(host=host, event=request_event).order_by(EventLog.event_time.desc())
        for log in eventLog:
            operation = log.operation
            sysinfo_id = log.sysinfo_id
            css = 'badge badge-grey '
            status = ''
            if operation is not None:
                if operation.startswith('error'):
                    status = 'error'
                    css = 'badge badge-important '
                elif operation.startswith('warning'):
                    status = 'warning'
                    css = 'badge badge-warning '
                else:
                    status = 'ok'
                    css = 'badge badge-success '
            status = log.status
            if status is None:
                status = ''
            if sysinfo_id is None:
                sysinfo_id = 0
            data = {
                'id': log.id,
                'event_id': log.event_id,
                'status': status,
                'operation': operation,
                'css': css,
                'event_time': log.event_time,
                'content': log.content,
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

        request_sysinfo_log = json.loads(request.values["sysinfo_log"])
        host = request.values["host"]
        if HostList.getHostInfo(host) is None:
           return 'error(no host info in db)'

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

        if not request_sysinfo_log['sys_date'] or request_sysinfo_log['sys_date'] is None:
            sysinfo_error.append('no sys_date')
            sysinfo_sys_date = 'error(no sys_date)'
        else:
            sysinfo_sys_date = request_sysinfo_log['sys_date']

        if not request_sysinfo_log['sys_time'] or request_sysinfo_log['sys_time'] is None:
            sysinfo_error.append('no sys_time')
            sysinfo_sys_time = 'error(no sys_time)'
        else:
            sysinfo_sys_time = request_sysinfo_log['sys_time']

        if not request_sysinfo_log['cpu'] or request_sysinfo_log['cpu'] is None:
            sysinfo_error.append('no cpu')
            sysinfo_cpu = 'error(cpu)'
        elif request_sysinfo_log['cpu'] > HostList.getHostInfo(sysinfo_host).max_cpu:
            sysinfo_warning.append('overload cpu')
            sysinfo_cpu = 'warning(overload cpu ' + request_sysinfo_log['cpu'] + ')'
        else:
            sysinfo_cpu = request_sysinfo_log['cpu']

        if not request_sysinfo_log['memory'] or request_sysinfo_log['memory'] is None:
            sysinfo_error.append('no memory')
            sysinfo_memory = 'error(no memory)'
        elif request_sysinfo_log['memory'] > HostList.getHostInfo(sysinfo_host).max_memory:
            sysinfo_warning.append('overload memory')
            sysinfo_memory = 'warning(overload memory' + request_sysinfo_log['memory'] + ')'
        else:
            sysinfo_memory = request_sysinfo_log['memory']

        if not request_sysinfo_log['disk'] or request_sysinfo_log['disk'] is None:
            sysinfo_error.append('no disk')
            sysinfo_disk = 'error(no disk)'
        elif len(request_sysinfo_log['disk']) > 0:
            is_warning = 0
            for info in request_sysinfo_log['disk']:
                if info['used'] > HostList.getHostInfo(sysinfo_host).max_disk:
                    sysinfo_warning.append('overload disk ' + info['partion'])
                    is_warning = 1
                    sysinfo_disk += 'overload disk ' + info['partion'] + ':' + info['used'] + '|'
                else:
                    sysinfo_disk += info['partion'] + ':' + info['used'] + '|'
            if is_warning == 1:
                sysinfo_disk = 'warning(' + sysinfo_disk + ')'

        if not request_sysinfo_log['service'] or request_sysinfo_log['service'] is None:
            sysinfo_error.append('no service')
            sysinfo_service = 'error(no service)'
        else:
            sysinfo_service = request_sysinfo_log['service']

        if not request_sysinfo_log['database'] or request_sysinfo_log['database'] is None or len(request_sysinfo_log['database']) == 0:
            sysinfo_error.append('no database')
            sysinfo_database = 'error(no database)'
        else:
            is_warning = 0
            is_error = 0
            for info in request_sysinfo_log['database']:
                dbtype = info['dbtype']
                cnn_cnt = info['cnn_cnt']
                dbname = info['dbname']
                dbinfo = dbtype + '/' + str(cnn_cnt) + '@' + dbname

                if cnn_cnt is None or len(str(cnn_cnt)) == 0:
                    sysinfo_error.append('can not be connected:' + dbinfo)
                    sysinfo_database += 'can not be connected:' + dbinfo + '|'
                    is_error = 1

                if cnn_cnt > HostList.getHostInfo(sysinfo_host).max_postgres:
                    sysinfo_database += 'overload connection:' + dbinfo + '|'
                    is_warning = 1
                else:
                    sysinfo_database += dbinfo + '|'

            if is_error == 1:
                sysinfo_database = 'error(' + sysinfo_database + ')'
            elif is_warning == 1:
                    sysinfo_database = 'warning(' + sysinfo_database + ')'

        sysinfo_operation = 'ok'
        if len(sysinfo_error) > 0:
            sysinfo_operation = 'error('
            for info in sysinfo_error:
                sysinfo_operation += info + '\n'
            sysinfo_operation += ')'
        if len(sysinfo_warning) > 0:
            sysinfo_operation = 'warning('
            for info in sysinfo_warning:
                sysinfo_operation += info + '\n'
            sysinfo_operation += ')'

        sysinfo_log = {
            'host': sysinfo_host,
            'sys_date': sysinfo_sys_date,
            'sys_time': sysinfo_sys_time,
            'cpu': sysinfo_cpu,
            'memory': sysinfo_memory,
            'disk': sysinfo_disk,
            'service': sysinfo_service,
            'database': sysinfo_database,
            'operation' : sysinfo_operation
        }
        sysinfo_id = SysInfoLog.insertSysInfoLog(sysinfo_log)

        event_logs=[]
        request_event_log = json.loads(request.values["event_log"])
        if not len(request_event_log) == 0:
            for log in request_event_log:
                eventList = EventList.query.filter_by(scheduled_type='day', event=log['event']).first()
                eventLog = EventLog.query.filter_by(host=host, event=log['event'], event_date=log['event_date'], type=log['type']).order_by(EventLog.event_time.desc()).first()

                operation=''

                if log['status'] == u'executing':
                    operation='ok(executing)'
                    if eventList.scheduled_start_time < log['event_time']:
                        operation ='warning(start delay)'
                elif log['status'] == u'done':
                    if not eventLog is None and eventLog.status == u'executing':
                        operation = 'ok(done)'
                        if eventList.scheduled_end_time < log['event_time']:
                            operation ='warning(end delay)'
                    else:
                        operation = 'error(no start)'
                elif log['status'] == u'error':
                    operation = 'error(custom error)'
                else:
                    operation = 'unknown'

                event_log = {
                    'host': host,
                    'event_id': log['event_id'],
                    'event_date': log['event_date'],
                    'event_time': log['event_time'],
                    'event': log['event'],
                    'type': log['type'],
                    'status': log['status'],
                    'content': log['content'],
                    'operation': operation,
                    'sysinfo_id': sysinfo_id
                }
                EventLog.insertEventLog(event_log)
    except Exception as ex:
        return str(ex)

    return 'ok'

@host.route('/showdetail/get-sysinfo-detail/<int:sysinfo_id>')
def getSysinfoDetail(sysinfo_id):
    process = request.args.get('process')
    if process is None:
        sysinfo = {}
        if sysinfo_id is not None and sysinfo_id != 0:
            sysinfolog = SysInfoLog.getSysInfoLogById(sysinfo_id)
            if sysinfolog is not None:
                sysinfo = {
                    'id': sysinfolog.id,
                    'host': sysinfolog.host,
                    'sys_date': sysinfolog.sys_date,
                    'sys_time': sysinfolog.sys_time,
                    'cpu': sysinfolog.cpu,
                    'memory': sysinfolog.memory,
                    'disk': sysinfolog.disk,
                    'service': sysinfolog.service,
                    'database': sysinfolog.database,
                    'operation': sysinfolog.operation
                }
        return jsonify({'sysinfo': sysinfo})
    else:
        id = request.args.get('id')
        event_id = request.args.get('event_id')
        comment = request.args.get('comment')
        operation = EventLog.getOperationById(id)
        detail = ''
        if not event_id is None and event_id != '':
            if not comment is None and comment != '':
                detail = event_id + ':' + comment
            else :
                detail = event_id
        else:
            if not comment is None and comment != '':
                detail = comment
        if detail != '' :
            detail = process + '(' + detail + ')'
        else :
            detail = process
        if not operation is None and operation != '':
            detail = detail + '-' + operation

        EventLog.updateOperationById(id, detail)
        return jsonify({'result': 'ok'})
