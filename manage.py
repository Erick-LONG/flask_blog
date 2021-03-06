#！/usr/bin/env python
# -*- coding:utf-8 -*-
import os
from app import create_app,db
from app.models import User,Role,Post,Follow,Permission,Comment
from flask_script import Manager,Shell
from flask_migrate import Migrate,MigrateCommand

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True,include='app/*')
    COV.start()

app=create_app(os.getenv('FLASK_CONFIG')or 'default')
manager = Manager(app)
# 数据库迁移
migrate = Migrate(app,db)
manager.add_command('db',MigrateCommand)
# 集成python shell
def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role,Post=Post,Follow=Follow,Permission=Permission,Comment=Comment)
manager.add_command("shell", Shell(make_context=make_shell_context))

@manager.command
def test(coverage=False):
    '''启动单元测试'''
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE']='1'
        os.execvp(sys.executable,[sys.executable] + sys.argv)# 设定完环境变量重启脚本

    import unittest
    tests=unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:
        COV.stop()
        COV.save()
        print('覆盖总计：')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir,'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML 版本：file://%s/index.html'% covdir)
        COV.erase()

    if os.path.exists('.env'):
        print('Importing environment from .env...')
        for line in open('.env'):
            var = line.strip().split('=')
            if len(var) == 2:
                os.environ[var[0]] = var[1]


@manager.command
def profile(length=25, profile_dir=None):
    """启动请求分析器"""
    # 使用python manage.py profile 启动程序，终端会显示每条请求的分析数据，其中包含了25个运行最慢的25个函数
    # --length 可修改函数显示数量
    # --profile_dir 可保存在指定目录下的文件中
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length], profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """执行部署任务"""
    from flask_migrate import upgrade
    from app.models import Role, User
    # 把数据库迁移到最新修订版本
    upgrade()
    # 创建用户角色
    Role.insert_roles()
    # 让所有用户都关注此用户
    User.add_self_follows()


if __name__ == '__main__':
    manager.run()
