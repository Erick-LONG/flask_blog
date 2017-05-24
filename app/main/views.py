#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import render_template,session,redirect,url_for,current_app
from . import main
from .forms import NameForm
from .. import db
from ..models import User
from ..email import send_mail
from flask import abort

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
		return redirect(url_for('.index')) # 蓝本中index函数在main.index下
	return render_template('index.html', name=session.get('name'), form=form, known=session.get('known',False))

# 举例演示使用权限检查装饰器
from app.decorators import admin_required,permission_required
from ..models import Permission
from flask_login import login_required

@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
	return 'For administrators'

@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderator_only():
	return 'For comment moderator'

@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	return render_template('user.html',user=user)