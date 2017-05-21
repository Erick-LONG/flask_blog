#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import render_template,session,redirect,url_for,current_app
from . import main
from .forms import NameForm
from .. import db
from ..models import User
from ..email import send_mail

# 使用蓝本自定义路由
@main.route('/', methods=['get', 'post'])
def index():
	#name = None
	form = NameForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.name.data).first()
		if user is None:
			user = User(username=form.name.data)
			db.session.add(user)
			session['known']=False
			if current_app.config['FLASKY_ADMIN']:
				send_mail(current_app.config['FLASKY_ADMIN'],'New user','mail/new_user',user=user)
		else:
			session['known'] = True
		session['name']=form.name.data
		form.name.data=''
		return redirect(url_for('.index')) # 蓝本中index函数在main.index下
	return render_template('index.html', name=session.get('name'), form=form, known=session.get('known',False))
