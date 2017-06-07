#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import jsonify
from . import api
from ..exceptions import ValidationError

def forbidden(message):
    response = jsonify({'error':'forbidden','message':message})
    response.status_code=403
    return response

def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response

def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response

@api.errorhandler(ValidationError)
# 全局异常处理程序，只有从蓝本中的路由抛出异常才会调用处理这个程序
def validation_error(e):
    return bad_request(e.args[0])