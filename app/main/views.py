#！/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import render_template,session,redirect,url_for,current_app,flash,abort,request,make_response
from . import main
from .forms import NameForm,EditProflieForm,EditProflieAdminForm,PostForm,CommentForm
from flask_login import login_required, current_user
from .. import db
from ..models import User,Role,Post,Comment
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
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed',''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    # 显示分页需要用到sqlachemy提供的paginate方法
    pagination=query.order_by(Post.timestamp.desc())\
        .paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    # 显示当前页面的记录
    posts = pagination.items
    return render_template('index.html',form=form,posts=posts,show_followed=show_followed,pagination=pagination)

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
@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        # current_user(上下文代理对象)._get_current_object() 真正的User对象
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('你已经发布了新评论.')
        # page设为-1，用来请求评论的最后一页，刚提交的评论才会出现在页面中
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    # 程序获取页数，发现时-1时，会计算总量和总页数得出真正显示的页数
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)

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
        return redirect(url_for('.post',id=post.id))
    form.body.data=post.body

    return render_template('edit_post.html',form=form)

# 用户点击关注按钮后执行/follow/<username>路由
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('你已经关注他了')
        return redirect(url_for('.user',username=username))
    current_user.follow(user)
    flash('关注成功')
    return redirect(url_for('.user',username=username))

# 用户点击取消关注按钮后执行/unfollow/<username>路由
@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('你还没有关注他')
        return redirect(url_for('.user',username=username))
    current_user.unfollow(user)
    flash('取消关注成功')
    return redirect(url_for('.user',username=username))

# 用户点击关注者数量后调用/followers/<username>
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    pagination = user.followers.paginate(page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                                         error_out=False)
    follows =[{'user':item.follower,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html',user=user,title='粉丝列表',
                           endpoint='.followers',pagination=pagination,follows=follows)


# 用户点击粉丝数量后调用/followed/<username>
@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('用户不存在')
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    pagination = user.followed.paginate(page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
    follows=[{'user':item.followed,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html',user=user,title='关注列表',
                           endpoint='.followed_by',pagination=pagination,follows=follows)

@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed','',max_age=30*24*60*60)
    return resp

@main.route('/followed')
@login_required
def show_followed():
    # cookies只能在响应中设置，需要用make_response创建响应对象
    resp = make_response(redirect(url_for('.index')))
    # max_age设定cookies的过期时间，30*24*60*60为30天
    resp.set_cookie('show_followed','1',max_age=30*24*60*60)
    return resp

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html',comments=comments,pagination=pagination,page=page)

@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))

@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))

# 当所有测试完成之后关闭服务器的路由
@main.route('/shutdown')
def server_shutdown():
    # 只有在测试环境中，当前路由可用
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down....'