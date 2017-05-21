#！/usr/bin/env python
# -*- coding:utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'  # 可以用来存储框架，扩展，程序等的配置变量
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 每次请求结束后自动提交数据库的变动
    FLASKY_MAIL_SUBJECT_PREFIX= '[Flasky]'
    FLASKY_MAIL_SENDER= 'Flasky Admin <flasky@example.com>'  # 发件人
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')  # 收件人

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG=True
    # 邮件配置
    MAIL_SERVER= 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD= os.environ.get('MAIL_PASSWORD')
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