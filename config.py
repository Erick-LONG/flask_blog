#！/usr/bin/env python
# -*- coding:utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))
class Config:
    SECRET_KEY = 'you do not know'  # os.environ.get('SECRET_KEY') or 可以用来存储框架，扩展，程序等的配置变量
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 每次请求结束后自动提交数据库的变动
    FLASKY_MAIL_SUBJECT_PREFIX= '[Flasky]'
    FLASKY_MAIL_SENDER= 'Flasky Admin <17601635180@163.com>'  # 发件人
    FLASKY_ADMIN = '834424581@qq.com' #os.environ.get('FLASKY_ADMIN') 收件人
    FLASKY_POSTS_PER_PAGE=15
    FLASKY_FOLLOWERS_PER_PAGE=15
    FLASKY_COMMENTS_PER_PAGE=15
    WTF_CSRF_ENABLED=False # 测试中禁用CSRF保护

    FLASK_SLOW_DB_QUERY_TIME=0.5
    SQLALCHEMY_RECORD_QUERIES=True # 启用缓慢查询记录功能的配置-启用记录查询统计数据的功能
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG=True
    # 邮件配置
    MAIL_SERVER= 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    MAIL_USERNAME ='17601635180@163.com' #os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD= 'LONGlong941110' #os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI= os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

class TestingConfig(Config):
    TESTING=True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir,'data-test.sqlite')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir,'data.sqlite')

config={
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,
    'default':DevelopmentConfig
}