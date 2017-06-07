#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import render_template,request,jsonify
from . import main

#主程序的errorhandler
@main.app_errorhandler(404)
def page_not_find(e):
    # 程序检查Accept请求首部request.accept_mimetypes，根据首部的值决定客户端期望接收的响应格式
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error':'not found'})
        response.status_code =404
        return response
    return render_template('404.html'),404

@main.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'),403

@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'),500

