#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import render_template,session,redirect,url_for,current_app,flash,abort,request
from . import main
from .forms import NameForm,EditProflieForm,EditProflieAdminForm,PostForm
from flask_login import login_required, current_user
from .. import db
from ..models import User,Role,Post
from ..email import send_mail
from flask import abort

from app.decorators import admin_required,permission_required
from ..models import Permission
from flask_login import login_required

# 使用蓝本自定义路由
@main.route('/', methods=['get', 'post'])
def index():
	form = PostForm()
	# 检查用户是否有写文章的权限并检查是否可以通过验证
	if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
		# current_user._get_current_object() 新文章对象，内含真正的用户对象
		post = Post(body = form.body.data,author=current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('.index'))
	#posts = Post.query.order_by(Post.timestamp.desc()).all()
	# 分页显示博客文章列表
	# 页数请求从查询字符串中获取，如果没有制定默认为第一页
	page = request.args.get('page',1,type=int)
	# 显示分页需要用到sqlachemy提供的paginate方法
	pagination=Post.query.order_by(Post.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
	# 显示当前页面的记录
	posts = pagination.items
	return render_template('index.html',form=form,posts=posts,pagination=pagination)

# 举例演示使用权限检查装饰器
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
	#user = User.query.filter_by(username=username).first_or_404()
	if user is None:
		abort(404)
	posts =user.posts.order_by(Post.timestamp.desc()).all()
	return render_template('user.html',user=user,posts=posts)

@main.route('/edit-profile',methods=['get','post'])
@login_required
def edit_profile():
	form = EditProflieForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location=form.location.data
		current_user.about_me=form.about_me.data
		db.session.add(current_user)
		flash('你的资料已经更新')
		return redirect(url_for('.user',username=current_user.username))
	form.name.data = current_user.name
	form.location.data=current_user.location
	form.about_me.data=current_user.about_me
	return render_template('edit_profile.html',form=form)

@main.route('/edit-profile/<int:id>',methods=['get','post'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form =EditProflieAdminForm(user=user)
	if form.validate_on_submit():
		user.email=form.email.data
		user.username=form.username.data
		user.confirmed=form.confirmed.data
		user.role =Role.query.get(form.role.data)
		user.name=form.name.data
		user.location=form.location.data
		user.about_me=form.about_me.data
		db.session.add(user)
		flash('资料已经更新')
		return redirect(url_for('.user',username = user.username))
	form.email.data=user.email
	form.username.data = user.username
	form.confirmed.data=user.confirmed
	# choice属性设置的元祖列表使用数字标识符表示各选项
	form.role.data=user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit_profile.html',form=form,user=user)

# 文章固定链接
@main.route('/post/<int:id>')
def post(id):
	post=Post.query.get_or_404(id)
	return render_template('post.html',post=[post])

# 编辑博客路由
@main.route('/edit/<int:id>',methods=['get','post'])
@login_required
def edit(id):
	post=Post.query.get_or_404(id)
	if current_user != post.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body=form.body.data
		db.session.add(post)
		flash('文章已经更新')
		return redirect(url_for('post',id=post.id))
	form.body.data=post.body
	return render_template('edit_post.html',form=form)

