# coding: utf-8
from flask import abort, render_template, redirect, request, jsonify
from . import host
from ..models import EventLog, HostList, EventList, SysInfoLog, PostLog
import json

@host.route('/hostlist')
def hostlist():
    hostinfo = HostList.getHostList()
    hostList = []
    for info in hostinfo:
        if info.host is not None and info.host != '':
            # 系统情报统计信息
            sys_ok_cnt = 0
            sys_warning_cnt = 0
            sys_error_cnt = 0
            items = ['cpu', 'memory', 'disk', 'service', 'database']
            for item in items:
                itemInfo = SysInfoLog.getItemInfo(info.host, item)
                if itemInfo is not None and len(itemInfo) > 0:
                    if itemInfo.startswith('error'):
                        sys_error_cnt = sys_error_cnt + 1
                    elif itemInfo.startswith('warning'):
                        sys_warning_cnt = sys_error_cnt + 1
                    else:
                        sys_ok_cnt = sys_ok_cnt + 1

            #业务情报统计信息
            event_ok_cnt = EventLog.getOkCnt(info.host)
            event_warning_cnt = EventLog.getWarningCnt(info.host)
            event_error_cnt = EventLog.getErrorCnt(info.host)
            event_unknown_cnt = EventLog.getUnknownCnt(info.host)

            data = {
                'host': info.host,
                'name': info.name,
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
    if host is None:
        return redirect('host/hostlist')
    # 获取主机名
    hostName = HostList.getHostInfo(host).name
    # 获取系统情报信息
    sysinfoList=[]
    items=['cpu', 'memory', 'disk', 'service', 'database']
    itemsname = {'cpu':u'CPU', 'memory':u'内存', 'disk':u'磁盘', 'service':u'服务', 'database':u'数据库'}
    # 最新系统情报更新时间
    sysDateTime = SysInfoLog.getItemInfo(host, 'date_time')
    for item in items:
        itemInfo = SysInfoLog.getItemInfo(host, item)
        info = []
        status = ''
        if itemInfo is not None:
            ia = itemInfo.split('|')
            for ii in ia:
                s = ''
                if ii != '':
                    if (ii.startswith('error')):
                        s = 'error'
                        status = 'error'
                        ii = ii[len(s)+1:len(ii)-1]
                    elif (ii.startswith('warning')):
                        s = 'warning'
                        if status != 'error':
                            status = 'warning'
                        ii = ii[len(s) + 1:len(ii) - 1]
                    else:
                        s = 'ok'
                        status = 'ok'

                info.append({'info':ii, 'status':s})

        data={
            'item': itemsname[item],
            'info': info,
            'status': status
        }
        sysinfoList.append(data)

    # 业务情报信息
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

    req_event = request.args.get('event')
    eventName = ''
    eventLogs=[]
    if req_event is not None:
        # 业务别业务情报列表
        event_log = EventLog.getRootEventLog(host, req_event)
        for log in event_log:
            status = log.status
            if status is None:
                status = ''
            data = {
                'id': log.id,
                'event_id': log.event_id,
                'status': status,
                'event_datetime': log.event_datetime,
                'content': log.content,
                'operation': log.operation,
                'operation_datetime': log.operation_datetime,
                'sysinfo_id': log.sysinfo_id
            }
            eventLogs.append(data)
        eventName = EventList.getDailyEventInfo(host, req_event).name
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
        sysinfo_sys_datetime = ''
        sysinfo_cpu = ''
        sysinfo_memory = ''
        sysinfo_disk = ''
        sysinfo_service = ''
        sysinfo_database = ''
        sysinfo_error=[]
        sysinfo_warning = []

        # 系统情报导入
        req_sys_datetime = request_sysinfo_log.get('sys_datetime')
        req_cpu = request_sysinfo_log.get('cpu')
        req_memory = request_sysinfo_log.get('memory')
        req_disk = request_sysinfo_log.get('disk')
        req_service = request_sysinfo_log.get('service')
        req_database = request_sysinfo_log.get('database')

        if req_sys_datetime is None or req_sys_datetime == '':
            sysinfo_sys_datetime = 'error(no sys_datetime)'
        else:
            sysinfo_sys_datetime = req_sys_datetime

        if req_cpu is None or req_cpu == '':
            sysinfo_cpu = 'error(not cpu)'
        elif float(req_cpu) > HostList.getHostInfo(sysinfo_host).max_cpu:
            sysinfo_cpu = 'warning(overload cpu : {0}%)'.format(req_cpu)
        else:
            sysinfo_cpu = "{0%}".fromat(req_cpu)

        if req_memory is None or req_memory == '':
            sysinfo_memory = 'error(no memory)'
        elif float(req_memory) > HostList.getHostInfo(sysinfo_host).max_memory:
            sysinfo_memory = 'warning(overload memory : {0}%)'.format(req_memory)
        else:
            sysinfo_memory = "{0%}".fromat(req_memory)

        if req_disk is None or req_disk == '':
            sysinfo_disk = 'error(no disk)'
        elif len(req_disk) > 0:
            for info in req_disk:
                if float(info.get('used')) > HostList.getHostInfo(sysinfo_host).max_disk:
                    sysinfo_disk += 'warning(overload disk : {0} : {1}%)|'.format(info.get('partion'), info.get('used'))
                else:
                    sysinfo_disk += '{0} : {1}%|'.format(info.get('partion'), info.get('used'))
            if (sysinfo_disk.endswith('|')):
                sysinfo_disk = sysinfo_disk[:len(sysinfo_disk)-1]

        if req_service is None or req_service == '':
            sysinfo_service = 'error(no service)'
        else:
            for info in req_service:
                cpu = 'cpu : {0}'.format(info.get('cpu'))
                create_time = 'create_time : {0}'.format(info.get('create_time'))
                pid = 'pid : {0}'.format(info.get('pid'))
                name = 'name : {0}'.format(info.get('name'))
                memory = 'memory : {0}'.format(info.get('memory'))
                sysinfo_service += '{0},{1},{2},{3},{4}|'.format(cpu, create_time, pid, name, memory)
            if (sysinfo_service.endswith('|')):
                sysinfo_service = sysinfo_service[:len(sysinfo_service)-1]

        if req_database is None or req_database == '':
            sysinfo_database = 'error(no database)'
        elif len(req_database) == 0:
            sysinfo_database = 'error(no instance in database)'
        else:
            for info in req_database:
                dbtype = info.get('dbtype')
                cnn_cnt = info.get('cnn_cnt')
                dbname = info.get('dbname')
                dbinfo = '{0} : {1} : {2}'.format(cnn_cnt, dbtype , dbname)

                if cnn_cnt is None or cnn_cnt == '':
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
            'sys_datetime': sysinfo_sys_datetime,
            'cpu': sysinfo_cpu,
            'memory': sysinfo_memory,
            'disk': sysinfo_disk,
            'service': sysinfo_service,
            'database': sysinfo_database
        }
        sysinfo_id = SysInfoLog.insertSysInfoLog(sysinfo_log)

        # 业务情报导入
        event_logs=[]
        request_event_log = json.loads(request.values['event_log'])
        if not len(request_event_log) == 0:
            for log in request_event_log:
                status = log.get('status')
                event_datetime = '{0} {1}'.format(log.get('event_date'), log.get('event_time'))
                eventinfo = EventList.getDailyEventInfo(host, log.get('event'))
                operation = 'unknown'
                if eventinfo is None:
                    operation = 'unknown'
                else:
                    if status == u'executing':
                        if eventinfo.scheduled_start_time is None:
                            operation = 'unknown'
                        else:
                            operation='ok(executing)'
                            if eventinfo.scheduled_start_time < log.get('event_time'):
                                operation ='warning(start delay)'
                    elif status == u'done':
                        if eventinfo.scheduled_end_time is None:
                            operation = 'unknown'
                        else:
                            operation = 'ok(done)'
                            if eventinfo.scheduled_end_time < log.get('event_time'):
                                operation ='warning(end delay)'
                    elif status == u'error':
                        operation = 'error(custom error)'
                event_log = {
                    'host': host,
                    'event_id': log.get('event_id'),
                    'event_datetime': event_datetime,
                    'event': log.get('event'),
                    'status': status,
                    'content': log.get('content'),
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
            itemInfo = SysInfoLog.getItemInfo(None, item, sysinfo_id)
            info = []
            istatus = ''
            if itemInfo is not None:
                ia = itemInfo.split('|')
                for ii in ia:
                    s = ''
                    if ii != '':
                        if (ii.startswith('error')):
                            s = 'error'
                            istatus = 'error'
                            ii = ii[len(s) + 1:len(ii) - 1]
                        elif (ii.startswith('warning')):
                            s = 'warning'
                            if istatus != 'error':
                                istatus = 'warning'
                            ii = ii[len(s) + 1:len(ii) - 1]
                        else:
                            s = 'ok'
                            status = 'ok'

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