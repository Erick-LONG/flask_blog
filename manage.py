#！/usr/bin/env python
# -*- coding:utf-8 -*-
import os
from app import create_app,db
from app.models import User,Role,Post
from flask_script import Manager,Shell
from flask_migrate import Migrate,MigrateCommand

app=create_app(os.getenv('FLASK_CONFIG')or 'default')
manager = Manager(app)
# 数据库迁移
migrate = Migrate(app,db)
manager.add_command('db',MigrateCommand)
# 集成python shell
def make_shell_context():
	return dict(app=app, db=db, User=User, Role=Role,Post=Post)
manager.add_command("shell", Shell(make_context=make_shell_context))



@manager.command
def test():
	'''启动单元测试'''
	import unittest
	tests=unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
	manager.run()


