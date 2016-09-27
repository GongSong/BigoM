#coding: utf-8
from datetime import datetime
from . import db

class EventLog(db.Model):
    __tablename__ = 'event_log'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(16))
    event_id = db.Column(db.String(16))
    event_datetime = db.Column(db.String(20))
    event = db.Column(db.String(16))
    status = db.Column(db.String(16))
    content = db.Column(db.Text)
    operation = db.Column(db.String(16))
    operation_type = db.Column(db.String(16))
    operation_datetime = db.Column(db.String(20))
    sysinfo_id = db.Column(db.Integer)

    def __repr__(self):
        return '<EventLog %r>' % self.host

    @staticmethod
    def getErrorCnt(host, event=None):
        if event is None:
            return EventLog.query.filter_by(host=host, operation_type='root').filter(
                EventLog.operation.like('error%')).group_by(EventLog.host, EventLog.event_id).count()
        else:
            return EventLog.query.filter_by(host=host, event=event, operation_type='root').filter(
                EventLog.operation.like('error%')).group_by(EventLog.host, EventLog.event_id).count()

    @staticmethod
    def getWarningCnt(host, event=None):
        if event is None:
            return EventLog.query.filter_by(host=host, operation_type='root').filter(
                EventLog.operation.like('warning%')).group_by(EventLog.host, EventLog.event_id).count()
        else:
            return EventLog.query.filter_by(host=host, event=event, operation_type='root').filter(
                EventLog.operation.like('warning%')).group_by(EventLog.host, EventLog.event_id).count()

    @staticmethod
    def getOkCnt(host, event=None):
        if event is None:
            return EventLog.query.filter_by(host=host, operation_type='root').filter(
                EventLog.operation.like('ok%')).group_by(EventLog.host, EventLog.event_id).count()
        else:
            return EventLog.query.filter_by(host=host, event=event, operation_type='root').filter(
                EventLog.operation.like('ok%')).group_by(EventLog.host, EventLog.event_id).count()

    @staticmethod
    def getAllCnt(host, event=None):
        if event is None:
            return EventLog.query.filter_by(host=host, operation_type='root').group_by(EventLog.host,
                                                                                       EventLog.event_id).count()
        else:
            return EventLog.query.filter_by(host=host, event=event, operation_type='root').group_by(EventLog.host,
                                                                                                    EventLog.event_id).count()

    @staticmethod
    def getUnknownCnt(host, event=None):
        allCnt = EventLog.getAllCnt(host, event)
        errorCnt = EventLog.getErrorCnt(host, event)
        warningCnt = EventLog.getWarningCnt(host, event)
        okCnt = EventLog.getOkCnt(host, event)
        return allCnt - errorCnt - warningCnt - okCnt

    @staticmethod
    def getLast(host, event):
        return EventLog.query.filter_by(host=host, event=event, operation_type='root').order_by(EventLog.operation_datetime.desc()).first()

    @staticmethod
    def getOperationHistory(event_id):
        return EventLog.query.filter_by(event_id=event_id, operation_type='branch').order_by(EventLog.operation_datetime.desc()).first()

    @staticmethod
    def insertEventLog(event_log):
        log = EventLog(
            host=event_log['host'],
            event_id=event_log['event_id'],
            event_datetime=event_log['event_datetime'],
            event=event_log['event'],
            status=event_log['status'],
            content=event_log['content'],
            operation=event_log['operation'],
            operation_type=event_log['operation_type'],
            operation_datetime=datetime.utcnow,
            sysinfo_id=event_log['sysinfo_id']
        )
        db.session.add(log)
        db.session.commit()

    @staticmethod
    def getOperationById(id):
        return EventLog.query.filter_by(id=id).one().operation

    @staticmethod
    def updateOperationById(id, operation):
        EventLog.query.filter_by(id=id).update({EventLog.operation:operation, EventLog.operation_datetime:datetime.utcnow})
        db.session.commit()

    @staticmethod
    def getOperationHistoryByEventId(event_id):
        return EventLog.query.filter_by(event_id=event_id, operation_type='branch').order_by(
            EventLog.operation_datetime.desc())

class SysInfoLog(db.Model):
    __tablename__ = 'sysinfo_log'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(16))
    sys_date = db.Column(db.String(16))
    sys_time = db.Column(db.String(16))
    cpu = db.Column(db.String(128))
    memory = db.Column(db.String(128))
    disk = db.Column(db.String(128))
    service = db.Column(db.String(128))
    database = db.Column(db.String(128))
    operation = db.Column(db.String(256))

    def __repr__(self):
        return '<SysInfoLog %r>' % self.host

    @staticmethod
    # def getSysInfoLog(host, day=0):
    #     return SysInfoLog.query.filter(SysInfoLog.host==host, SysInfoLog.sys_date>=(datetime.date.today()-datetime.timedelta(day))).order_by(SysInfoLog.sys_date.desc(), SysInfoLog.sys_time.desc()).first()
    def getSysInfoLog(host):
        return SysInfoLog.query.filter_by(host=host).order_by(SysInfoLog.sys_date.desc(), SysInfoLog.sys_time.desc()).first()

    @staticmethod
    def getSysInfoLogById(id):
        return SysInfoLog.query.filter_by(id=id).one()

    @staticmethod
    def getItemInfo(host, item):
        sysInfo = SysInfoLog.query.filter_by(host=host).order_by(SysInfoLog.sys_date.desc(),
                                                       SysInfoLog.sys_time.desc()).first()
        if not sysInfo is None:
            if item == 'cpu' and not sysInfo.cpu is None:
                return sysInfo.cpu
            elif item == 'memory' and not sysInfo.memory is None:
                return sysInfo.memory
            elif item == 'disk' and not sysInfo.disk is None:
                return sysInfo.disk
            elif item == 'service' and not sysInfo.service is None:
                return sysInfo.service
            elif item == 'database' and not sysInfo.database is None:
                return sysInfo.database
            elif item == 'date_time' and not sysInfo.sys_date is None and not sysInfo.sys_time is None:
                return sysInfo.sys_date + ' ' + sysInfo.sys_time
            else:
                return ''
        else:
            return ''
    @staticmethod
    def insertSysInfoLog(sysinfo_log):
        log = SysInfoLog(
            host = sysinfo_log['host'],
            sys_date = sysinfo_log['sys_date'],
            sys_time = sysinfo_log['sys_time'],
            cpu = sysinfo_log['cpu'],
            memory = sysinfo_log['memory'],
            disk = sysinfo_log['disk'],
            service = sysinfo_log['service'],
            database = sysinfo_log['database']
        )
        db.session.add(log)
        db.session.commit()
        return log.id

class HostList(db.Model):
    __tablename__ = 'host_list'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(16))
    name = db.Column(db.String(32))
    max_cpu = db.Column(db.String(8))
    max_memory = db.Column(db.String(8))
    max_disk = db.Column(db.String(8))
    max_postgres = db.Column(db.Integer)
    max_mysql = db.Column(db.Integer)

    @staticmethod
    def getHostInfo(host):
        return HostList.query.filter_by(host=host).first()

class EventList(db.Model):
    __tablename__ = 'event_list'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(16))
    event = db.Column(db.String(16))
    name = db.Column(db.String(16))
    scheduled_start_time = db.Column(db.String(8))
    scheduled_end_time = db.Column(db.String(8))
    scheduled_type = db.Column(db.String(8))
    sort = db.Column(db.Integer)
    ok_cnt = db.Column(db.Integer)
    err_cnt = db.Column(db.Integer)
    war_cnt = db.Column(db.Integer)
    last_time = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def getDailyEventList(host):
        if EventList.query.filter_by(host=host,scheduled_type='day').order_by(EventList.sort.asc()).count() == 0:
            return EventList.query.filter_by(host=None,scheduled_type='day').order_by(EventList.sort.asc())
        else:
            return EventList.query.filter_by(host=host,scheduled_type='day').order_by(EventList.sort.asc())