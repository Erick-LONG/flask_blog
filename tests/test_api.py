#！/usr/bin/env python
# -*- coding:utf-8 -*-
import unittest
from app import create_app,db
from app.models import User,Role
from flask import url_for
import re,json
import base64

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_api_headers(self,username,password):
        return {
            'Authorization':'Basic' + base64.b64encode((username+':'+password).encode('utf-8')).decode('utf-8'),
            'Accept':'application/json',
            'Content-Type':'application/json'
        }
    def test_no_auth(self):
        response = self.client.get(url_for('api.get_posts'),content_type='application/json')
        self.assertTrue(response.status_code ==401)

    def test_posts(self):
        # 添加一个用户
        r = Role.query.fliter_by(name = 'User').first()
        self.assertIsNotNone(r)
        u = User(email = 'bababa@qq.com',password = 'abc',confirmed = True,role = r)
        db.session.add(u)
        db.session.commit()

        # 写一篇文章
        response = self.client.post(url_for('api.new_post'),
                                    headers = self.get_api_headers('bababa@qq.com','abc'),
                                    data = json.dumps({'body':'body of the blog'}) )
        self.assertTrue(response.status_code ==201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # 获取刚发布文章
        response = self.client.get(url,headers = self.get_api_headers('bababa@qq.com','abc'))
        self.assertTrue(response.status_code ==200)
        # 测试客户端不会自动json编码解码
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['url']==url)
        self.assertTrue(json_response['body']=='body of the blog')
        self.assertTrue(json_response['body_html'=='<p>body of blog post</p>'])
