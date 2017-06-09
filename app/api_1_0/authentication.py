# ！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask_httpauth import HTTPBasicAuth
from flask import g, jsonify
from ..models import AnonymousUser, User
from .errors import unauthorized, forbidden
from . import api

auth = HTTPBasicAuth()

@auth.verify_password
def vertify_password(email_or_token, password):
    if email_or_token == '':
        g.current_user = AnonymousUser()
        return True
    if password == '':
        # 如果密码为空假定参数时令牌，按照令牌去认证
        g.current_user = User.verify_auth_token(email_or_token)
        # 为避免客户端用旧令牌申请新令牌，如果使用令牌认证就拒绝请求
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    # 为了让视图函数区分两种认证方法 添加了token_used变量
    g.token_used = False
    return user.verify_password(password)


# 认证失败调用401处理程序
@auth.error_handler
def auth_error():
    return unauthorized('无效认证')


# 为保护路由需调用auth.login_required修饰器
# @api.route('/posts/')
# @auth.login_required
# def get_posts():
#     pass

# 为所有的路由进行相同方式的登陆验证保护
@api.before_request
@auth.login_required
def before_request():
    # 拒绝已通过认证但是没有确认的账户
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('账户未确认')


# 生成认证令牌
@api.route('/token')
def get_token():
    # 为避免客户端用旧令牌申请新令牌，如果使用令牌认证就拒绝请求
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('无效认证')
    return jsonify({'token': g.current_user.generate_auth_token(expiration=3600), 'expiration': 3600})

