#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import render_template,redirect,request,url_for,flash
from flask_login import login_user,login_required,logout_user,current_user
from . import auth
from ..models import User
from .forms import LoginForm,RegistrationForm,ChangePasswordForm,PasswordResetRequestForm, PasswordResetForm,ChangeEmailForm
from .. import db
from ..email import send_mail

@auth.route('/login',methods=['get','post'])
def login():
	form = LoginForm()
	if form.validate_on_submit(): # 验证表单数据
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user,form.remember_me.data) # 如果为True则为用户生成长期有效的cookies
			return redirect(request.args.get('next') or url_for('main.index'))# next保存原地址(从request.args字典中读取)
		flash('用户名或密码无效')
	return render_template('auth/login.html',form=form)

@auth.route('/logout')
@login_required
def logout():
	logout_user()
	flash('你已经退出')
	return redirect(url_for('main.index'))

@auth.route('/register',methods=['get','post'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user=User(email = form.email.data,
				  username=form.username.data,
				  password=form.password.data)
		db.session.add(user)
		db.session.commit()
		token = user.generate_confirmation_token()
		send_mail(user.email,'确认你的账户','auth/email/confirm',user=user,token=token)
		flash('我们已经给你发送了一封确认邮件')
		return redirect(url_for('main.index'))
	return render_template('auth/register.html',form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
	if current_user.confirmed:
		return redirect(url_for('main.index'))
	if current_user.confirm(token):
		flash('你已经确认了你的账户，谢谢')
	else:
		flash('确认链接失效或过期')
	return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
	if current_user.is_authenticated\
			and not current_user.confirmed \
			and request.endpoint[:5] != 'auth.'\
			and request.endpoint != 'static':
		return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
	if current_user.is_anonymous or current_user.confirmed:
		return redirect(url_for('main.index'))
	return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
	token=current_user.generate_confirmation_token()
	send_mail(current_user.email,'确认你的账户','auth/email/confirm',user=current_user,token=token)
	flash('一封新的确认邮件已经发送到您的邮箱')
	return redirect(url_for('main.index'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
	form = ChangePasswordForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.old_password.data):
			current_user.password = form.password.data
			db.session.add(current_user)
			flash('你的密码已经更新')
			return redirect(url_for('main.index'))
		else:
			flash('无效的密码.')
	return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = PasswordResetRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			token = user.generate_reset_token()
			send_mail(user.email, '重置你的密码',
					   'auth/email/reset_password',
					   user=user, token=token,
					   next=request.args.get('next'))
		flash('一封重置密码的邮件已经发给您的邮箱了')
		return redirect(url_for('auth.login'))
	return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = PasswordResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is None:
			return redirect(url_for('main.index'))
		if user.reset_password(token, form.password.data):
			flash('你的密码已经重置')
			return redirect(url_for('auth.login'))
		else:
			return redirect(url_for('main.index'))
	return render_template('auth/reset_password.html', form=form)

@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
	form = ChangeEmailForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.password.data):
			new_email = form.email.data
			token = current_user.generate_email_change_token(new_email)
			send_mail(new_email, 'Confirm your email address',
					   'auth/email/change_email',
					   user=current_user, token=token)
			flash('一封确认您新邮件地址的邮件已经发给您的邮箱了.')
			return redirect(url_for('main.index'))
		else:
			flash('无效的邮箱或密码.')
	return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
	if current_user.change_email(token):
		flash('邮箱地址已更新.')
	else:
		flash('无效的请求')
	return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        # 不在认证蓝本中
        if not current_user.confirmed and request.endpoint[:5] !='auth.' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

@auth.before_app_first_request
def before_request():
	if current_user.is_authenticated:
		current_user.ping()
		if not current_user.confirmed and request.endpoint[:5] !='auth.': # 不在认证蓝本中
			return redirect(url_for('auth.unconfirmed'))

