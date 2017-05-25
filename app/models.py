#！/usr/bin/env python
# -*- coding:utf-8 -*-
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin # 匿名用户角色
from . import login_manager
from flask_login import login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app,request
from . import db
from datetime import datetime
import hashlib
# 加载用户的回调函数
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

# #保护路由
# @app.route('/secret')
# @login_required
# def secret():
# 	return '只有认证后的用户才能登陆'

class Role(db.Model):
	__tablename__='roles'
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(64),unique=True)
	default = db.Column(db.Boolean,default=False,index=True) # 默认角色
	permissions = db.Column(db.Integer)# 位标志，各个操作都对应一个位位置，能执行某项操作的角色，其位会被设为1
	users = db.relationship('User',backref='role',lazy='dynamic') # 不加载记录，但是提供加载记录的查询
	@staticmethod
	def insert_roles():
		roles = {
			'User':(Permission.FOLLOW |
					Permission.COMMENT|
					Permission.WRITE_ARTICLES,True),
			'Moderator':(Permission.FOLLOW |
						 Permission.COMMENT |
						 Permission.WRITE_ARTICLES |
						 Permission.MODERATE_COMMENTS,False),
			'Administrator':(0xff,False)

		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()# 先根据角色名查找现有的角色，然后再更新
			if role is None:# 如果没有该角色名时才会创建新角色
				role=Role(name=r) # 创建新角色
			role.permissions=roles[r][0] # 设置该角色对应的权限
			role.default=roles[r][1] # 设置该角色对应权限的默认值
			db.session.add(role) # 添加到数据库
		db.session.commit() # 提交数据库

	def __repr__(self):
		return '<Role %r>'% self.name

class User(UserMixin,db.Model):
	def __init__(self,**kwargs):
		super(User,self).__init__(**kwargs)# 调用父类的构造函数
		if self.role is None: # 如果创建父类对象之后还没有定义角色
			if self.email==current_app.config['FLASKY_ADMIN']:# 根据电子邮件地址
				self.role=Role.query.filter_by(permissions=0xff).first() # 设置其为管理员
			if self.role is None: # 或者设置为默认角色
				self.role=Role.query.filter_by(default=True).first()

		if self.email is not None and self.avatar_hash is None:
			self.avatar_hash=hashlib.md5(self.email.encode('utf-8')).hexdigest()

	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	email=db.Column(db.String(64),unique=True,index=True)
	username = db.Column(db.String(64), unique=True,index=True)
	role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))
	password_hash=db.Column(db.String(128))
	confirmed = db.Column(db.Boolean,default=False)
	name = db.Column(db.String(64))
	location = db.Column(db.String(64))
	about_me = db.Column(db.Text())  # 和String的区别是不需要指定最大长度
	member_since = db.Column(db.DateTime(), default=datetime.utcnow)  # default 可以接受函数为默认值，在需要的时候回自定调用指定的函数，所以不需要加（）
	last_seen= db.Column(db.DateTime(), default=datetime.utcnow)  # 初始值是当前时间
	avatar_hash = db.Column(db.String(32))# 头像哈希值存储到数据库
	@property
	def password(self):
		raise AttributeError('密码不是一个可读属性') #只写属性
	@password.setter
	def password(self,password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self,password):
		return check_password_hash(self.password_hash,password)

	def generate_confirmation_token(self,expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'],expiration)
		return s.dumps({'confirm':self.id})
	def confirm(self,token):
		s=Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') !=self.id:
			return False
		self.confirmed=True
		db.session.add(self)
		return True

	def generate_reset_token(self, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'reset': self.id})

	def reset_password(self, token, new_password):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('reset') != self.id:
			return False
		self.password = new_password
		db.session.add(self)
		return True

	def generate_email_change_token(self, new_email, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'change_email': self.id, 'new_email': new_email})

	def change_email(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('change_email') != self.id:
			return False
		new_email = data.get('new_email')
		if new_email is None:
			return False
		if self.query.filter_by(email=new_email).first() is not None:
			return False
		self.email = new_email
		self.avatar_hash=hashlib.md5(self.email.encode('utf-8')).hexdigest()
		db.session.add(self)
		return True

	@login_manager.user_loader
	def load_user(user_id):
		return User.query.get(int(user_id))
	def can(self,permissions):
		# 在请求和赋予角色这两种权限进行位的“与”运算，如果成立，则允许用户执行此项操作
		return self.role is not None and \
			   (self.role.permissions & permissions)==permissions
	def is_administrator(self): # 认证为管理员角色判断
		return self.can(Permission.ADMINISTER)

	def ping(self):
		self.last_seen = datetime.utcnow()  # 获取当前时间
		db.session.add(self)  # 提交时间到数据库

	def gravatar(self,size=100,default='identicon',rating='g'):
		if request.is_secure:
			url = 'https://secure.gravatar.com/avatar'
		else:
			url='http://www.gravatar.com/avatar'
		hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
		return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url,hash=hash,size=size,default=default,rating=rating)

	def __repr__(self):
		return '<User %r>' % self.username

class Permission:
	FOLLOW=0x01
	COMMENT=0x02
	WRITE_ARTICLES=0x04
	MODERATE_COMMENTS=0x08
	ADMINISTER=0x80

class AnonymousUser(AnonymousUserMixin):
	def can(self, permissions):
		return False
	def is_administrator(self):
		return False
# 用户未登录时current_user的值，并且不用用户登陆即可检查用户权限
login_manager.anonymous_user=AnonymousUser