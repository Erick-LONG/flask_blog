#！/usr/bin/env python
# -*- coding:utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))
class Config:
    SECRET_KEY = 'you do not know'  # os.environ.get('SECRET_KEY') or 可以用来存储框架，扩展，程序等的配置变量
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 每次请求结束后自动提交数据库的变动
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    MAIL_USERNAME = '17601635180@163.com'  # os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = 'LONGlong941110'  # os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX= '[Flasky]'
    FLASKY_MAIL_SENDER= 'Flasky Admin <17601635180@163.com>'  # 发件人
    FLASKY_ADMIN = '834424581@qq.com' #os.environ.get('FLASKY_ADMIN') 收件人
    FLASKY_POSTS_PER_PAGE=15
    FLASKY_FOLLOWERS_PER_PAGE=15
    FLASKY_COMMENTS_PER_PAGE=15
    WTF_CSRF_ENABLED=False # 测试中禁用CSRF保护
    SSL_DISABLE=True # 配置是否使用SSL
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

    @classmethod
    def init_app(cls,app):
        Config.init_app(app)

        # 把错误通过电子邮件发送给管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls,'MAIL_USERNAME',None) is not None:
            credentials = (cls.MAIL_USERNAME,cls.MAIL_PASSWORD)
            if getattr(cls,'MAIL_USE_TLS',None):
                secure=()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER,cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX+'Application Error',
            credentials=credentials,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

class HerokuConfig(ProductionConfig):
    SSL_DISABLE=bool(os.environ.get('SSL_DISABLE'))
    @classmethod
    def init_app(cls,app):
        ProductionConfig.init_app(app)
        # 输出到stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

        # 处理代理服务器的首部
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app=ProxyFix(app.wsgi_app)

class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        # 写入系统日志
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config={
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,
    'default':DevelopmentConfig,
    'heroku': HerokuConfig,
    'unix': UnixConfig,
}