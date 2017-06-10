#！/usr/bin/env python
# -*- coding:utf-8 -*-
import unittest
from app import create_app,db
from app.models import User,Role
from flask import url_for
import re
class FlaskClientCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        # 测试客户端对象，use_cookies可保存cookies记住上下文
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get(url_for('main.index'))
        # as_text = True得到易于处理的字符串而不是字节数组
        self.assertTrue('访客' in response.get_data(as_text = True))

    def test_register_and_login(self):
        # 注册新账户
        respose = self.client.post(url_for('auth.register'),data = {'email':'papapa@qq.com','username':'papapa','password':'abc','password2':'abc'})
        self.assertTrue(respose.status_code ==302)

        # 使用新注册的账户登陆
        respose = self.client.post(url_for('auth.login'),data ={'email':'papapa@qq.com','password':'abc'},follow_redirects=True)
        data = respose.get_data(as_text=True)
        self.assertTrue(re.search('你好，\s+papapa!',data))
        self.assertTrue('你还没有确认你的邮件信息' in data)

        # 发送确认令牌
        user = User.query.fliter_by(email ='papapa@qq.com').first()
        token = user.generate_confirmation_token()
        respose = self.client.get(url_for('auth.confirm',token=token),follow_redirects = True)
        data = respose.get_data(as_text=True)
        self.assertTrue('你已经确认了你的账户' in data)

        # 退出
        respose = self.client.get(url_for('auth.logout'),follow_redirects = True)
        data = respose.get_data(as_text=True)
        self.assertTrue('你已经退出' in data)