#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import Flask
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
bootstrap = Bootstrap()
mail =Mail()
moment = Moment()
db = SQLAlchemy()
#初始化Flask-Login
login_manager=LoginManager()
login_manager.session_protection='strong' # 记录客户端ip，用户代理信息，发现异动，登出用户
login_manager.login_view='auth.login' # 设置登录页面端点，蓝本的名字也要加到前面


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    # 附加使用蓝本路由和错误页面
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint,url_prefix='/auth')
    return app

