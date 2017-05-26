#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,TextAreaField,BooleanField,SelectField
from wtforms.validators import DataRequired,Length,Email,Regexp
from ..models import User,Role
from wtforms import ValidationError

class NameForm(FlaskForm):
	name = StringField('姓名', validators=[DataRequired()])
	submit = SubmitField('提交')

class EditProflieForm(FlaskForm):
	name = StringField('真实姓名', validators=[Length(0,64)])
	location = StringField('位置', validators=[Length(0,64)])
	about_me = TextAreaField('关于我')
	submit = SubmitField('提交')

class EditProflieAdminForm(FlaskForm):
	email=StringField('邮箱', validators=[DataRequired(), Length(1, 64),Email()])
	username = StringField('用户名', validators=[DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'用户名必须是字母，数字，点号，下划线')])
	confirmed = BooleanField('确认')
	role = SelectField('角色',coerce=int)# 因为角色id是个整数，所以把字段值转化为整数而不是字符串
	name = StringField('真实姓名', validators=[Length(0, 64)])
	location = StringField('位置', validators=[Length(0, 64)])
	about_me = TextAreaField('关于我')
	submit = SubmitField('提交')
	def __init__(self,user,*args,**kwargs):
		super(EditProflieAdminForm,self).__init__(*args,**kwargs)
		#选项由元祖组成，选项的标识符和显示空间中的文本字符串
		self.role.choices=[(role.id,role.name) for role in Role.query.order_by(Role.name).all()]
		self.user=user
	def validate_email(self, filed):
		#首先检查字段是否发生了变化，并保证新值不和其他用户的字段值重复
		if filed.data != self.user.email and User.query.filter_by(email=filed.data).first():
			raise ValidationError('邮箱已被注册')

	def validate_username(self, filed):
		# 首先检查字段是否发生了变化，并保证新值不和其他用户的字段值重复
		if filed.data != self.username and User.query.filter_by(username=filed.data).first():
			raise ValidationError('用户名已被使用')

class PostForm(FlaskForm):
	body = TextAreaField('你在想什么？',validators=[DataRequired()])
	submit = SubmitField('提交')