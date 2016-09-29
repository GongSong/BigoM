#!/usr/bin/env python
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
from app import create_app, db
from app.models import EventLog, EventList, HostList, PostLog, SysInfoLog

app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

def make_shell_context():
    return dict(db=db)

manager.add_command("shell", Shell(make_context=make_shell_context))

@manager.command
def deploy(deploy_type):
    from flask.ext.migrate import upgrade

    # upgrade database to the latest version
    upgrade()

    if deploy_type == 'product':
        EventList.initData()
        HostList.initData()

if __name__ == '__main__':
    manager.run()
