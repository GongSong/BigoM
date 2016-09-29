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
                EventLog.operation.like('error%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()
        else:
            return EventLog.query.filter_by(host=host, event=event, operation_type='root').filter(
                EventLog.operation.like('error%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()

    @staticmethod
    def getWarningCnt(host, event=None):
        if event is None:
            return EventLog.query.filter_by(host=host, operation_type='root').filter(
                EventLog.operation.like('warning%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()
        else:
            return EventLog.query.filter_by(host=host, event=event, operation_type='root').filter(
                EventLog.operation.like('warning%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()

    @staticmethod
    def getOkCnt(host, event=None):
        if event is None:
            okCnt = EventLog.query.filter_by(host=host, operation_type='root').filter(
                EventLog.operation.like('ok%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()
            fixCnt = EventLog.query.filter_by(host=host, operation_type='root').filter(
                EventLog.operation.like('fix%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()
            ignorCnt = EventLog.query.filter_by(host=host, operation_type='root').filter(
                EventLog.operation.like('ignor%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()
            return okCnt + fixCnt + ignorCnt
        else:
            okCnt = EventLog.query.filter_by(host=host, event=event, operation_type='root').filter(
                EventLog.operation.like('ok%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()
            fixCnt = EventLog.query.filter_by(host=host, event=event, operation_type='root').filter(
                EventLog.operation.like('fix%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()
            ignorCnt = EventLog.query.filter_by(host=host, event=event, operation_type='root').filter(
                EventLog.operation.like('ignor%')).group_by(EventLog.host, EventLog.event_id, EventLog.status).count()
            return okCnt + fixCnt + ignorCnt

    @staticmethod
    def getAllCnt(host, event=None):
        if event is None:
            return EventLog.query.filter_by(host=host, operation_type='root').group_by(EventLog.host, EventLog.event_id, EventLog.status).count()
        else:
            return EventLog.query.filter_by(host=host, event=event, operation_type='root').group_by(EventLog.host, EventLog.event_id, EventLog.status).count()

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
    def getRootEventLog(host, event):
        return EventLog.query.filter_by(host=host, event=event, operation_type='root').order_by(EventLog.event_datetime.desc())

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
            operation_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            sysinfo_id=event_log['sysinfo_id']
        )
        db.session.add(log)
        db.session.commit()

    @staticmethod
    def getOperationById(id):
        return EventLog.query.filter_by(id=id).one().operation

    @staticmethod
    def updateOperationById(log_id, operation):
        EventLog.query.filter_by(id=log_id).update({EventLog.operation:operation, EventLog.operation_datetime:datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        db.session.commit()
        return EventLog.query.filter_by(id=log_id).one()

    @staticmethod
    def getOperationHistoryByEventId(event_id, log_id):
        return EventLog.query.filter_by(event_id=event_id, operation=log_id, operation_type='branch').order_by(EventLog.operation_datetime.desc())

class SysInfoLog(db.Model):
    __tablename__ = 'sysinfo_log'
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(16))
    sys_datetime = db.Column(db.String(20))
    cpu = db.Column(db.String(128))
    memory = db.Column(db.String(128))
    disk = db.Column(db.String(128))
    service = db.Column(db.Text)
    database = db.Column(db.String(128))

    def __repr__(self):
        return '<SysInfoLog %r>' % self.host

    @staticmethod
    def getSysInfoLog(host):
        return SysInfoLog.query.filter_by(host=host).order_by(SysInfoLog.sys_datetime.desc()).first()

    @staticmethod
    def getSysInfoLogById(id):
        if SysInfoLog.query.filter_by(id=id).count() > 0:
            return SysInfoLog.query.filter_by(id=id).one()
        else:
            return None

    @staticmethod
    def getItemInfo(host, item, id=None):
        if id is None:
            sysInfo = SysInfoLog.query.filter_by(host=host).order_by(SysInfoLog.sys_datetime.desc()).first()
        else:
            sysInfo = SysInfoLog.getSysInfoLogById(id)
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
            elif item == 'date_time' and not sysInfo.sys_datetime is None:
                return sysInfo.sys_datetime
            else:
                return ''
        else:
            return ''

    @staticmethod
    def insertSysInfoLog(sysinfo_log):
        log = SysInfoLog(
            host = sysinfo_log['host'],
            sys_datetime = sysinfo_log['sys_datetime'],
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
    max_cpu = db.Column(db.Integer)
    max_memory = db.Column(db.Integer)
    max_disk = db.Column(db.Integer)
    max_postgres = db.Column(db.Integer)
    max_mysql = db.Column(db.Integer)

    @staticmethod
    def getHostInfo(host):
        return HostList.query.filter_by(host=host).first()

    @staticmethod
    def getHostList():
        return HostList.query

    @staticmethod
    def initData():
        data = HostList(
            max_cpu = 50,
            max_disk = 50,
            max_memory = 50,
            max_postgres = 50,
            max_mysql = 50
        )
        db.session.add(data)
        db.session.commit()

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

    @staticmethod
    def getDailyEventList(host):
        if host is None or host == '' or EventList.query.filter_by(host=host, scheduled_type='day').order_by(EventList.sort.asc()).count() == 0:
            return EventList.query.filter_by(host=None, scheduled_type='day').order_by(EventList.sort.asc())
        else:
            return EventList.query.filter_by(host=host, scheduled_type='day').order_by(EventList.sort.asc())

    @staticmethod
    def getDailyEventInfo(host, event):
        if host is None or host == '' or EventList.query.filter_by(host=host, event=event, scheduled_type='day').order_by(EventList.sort.asc()).count() == 0:
            return EventList.query.filter_by(host=None, event=event, scheduled_type='day').first()
        else:
            return EventList.query.filter_by(host=host, event=event, scheduled_type='day').first()

    @staticmethod
    def initData():
        data = EventList(
            event = 'dbs',
            name = u'数据接入',
            scheduled_type = 'day',
            sort = 1
        )
        db.session.add(data)

        data = EventList(
            event = 'etl',
            name = u'数据清理',
            scheduled_type = 'day',
            sort = 2
        )
        db.session.add(data)

        data = EventList(
            event = 'mrg',
            name = u'数据合并',
            scheduled_type = 'day',
            sort = 3
        )
        db.session.add(data)

        data = EventList(
            event = 'tag_before',
            name = u'标签预处理',
            scheduled_type = 'day',
            sort = 4
        )
        db.session.add(data)

        data = EventList(
            event = 'tag',
            name = u'CLV模型',
            scheduled_type = 'day',
            sort = 5
        )
        db.session.add(data)

        data = EventList(
            event = 'tag_after',
            name = u'标签生成',
            scheduled_type = 'day',
            sort = 6
        )
        db.session.add(data)

        data = EventList(
            event = 'mkt',
            name = u'天机模型',
            scheduled_type = 'day',
            sort = 7
        )
        db.session.add(data)

        data = EventList(
            event = 'mkt_rpt',
            name = u'天机报表',
            scheduled_type = 'day',
            sort = 8
        )
        db.session.add(data)

        data = EventList(
            event = 'xj_rwd',
            name = u'玄机数据生成',
            scheduled_type = 'day',
            sort = 9
        )
        db.session.add(data)

        db.session.commit()

class PostLog(db.Model):
    __tablename__ = 'post_log'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text)
    exception = db.Column(db.Text)

    @staticmethod
    def insertPostLog(data, exception):
        log = PostLog(
            data=data,
            exception=exception
        )
        db.session.add(log)
        db.session.commit()