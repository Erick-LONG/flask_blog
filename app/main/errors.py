#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import render_template
from . import main

#主程序的errorhandler
@main.errorhandler(404)
def page_not_find(e):
	return render_template('404.html'), 404

@main.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500