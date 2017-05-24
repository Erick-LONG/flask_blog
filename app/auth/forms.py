#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import DataRequired,Length,Email,Regexp,EqualTo
from ..models import User
from wtforms import ValidationError
class LoginForm(FlaskForm):
    email=StringField('邮箱',validators=[DataRequired(),Length(1,64),Email()])
    password=PasswordField('密码',validators=[DataRequired()])
    remember_me=BooleanField('保持登陆')
    submit = SubmitField('登陆')

class RegistrationForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64), Email()])
    username= StringField('用户名', validators=[DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'用户名必须是字母，数字，点号，下划线')])
    password = PasswordField('密码', validators=[DataRequired(),EqualTo('password2',message='密码不一致')])
    password2 =  PasswordField('再次输入密码', validators=[DataRequired()])
    submit = SubmitField('注册')
    def validate_email(self,filed):
        if User.query.filter_by(email=filed.data).first():
            raise ValidationError('邮箱已被注册')
    def validate_username(self,filed):
        if User.query.filter_by(username=filed.data).first():
            raise ValidationError('用户名已被使用')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='密码必须一致')])
    password2 = PasswordField('再次确认新密码', validators=[DataRequired()])
    submit = SubmitField('更新密码')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    submit = SubmitField('重置密码')

class PasswordResetForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),Email()])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='密码必须一致')])
    password2 = PasswordField('再次确认密码', validators=[DataRequired()])
    submit = SubmitField('重置密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('未知的邮箱地址')

class ChangeEmailForm(FlaskForm):
    email = StringField('新邮箱', validators=[DataRequired(), Length(1, 64),
                                                 Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('更新邮件地址')
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已经注册过了')