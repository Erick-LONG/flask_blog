# ！/usr/bin/env python
# -*- coding:utf-8 -*-
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin  # 匿名用户角色
from . import login_manager
from flask_login import login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from . import db
from datetime import datetime
import hashlib
from markdown import markdown
import bleach
from app.exceptions import ValidationError


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
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)  # 默认角色
    permissions = db.Column(db.Integer)  # 位标志，各个操作都对应一个位位置，能执行某项操作的角色，其位会被设为1
    users = db.relationship('User', backref='role', lazy='dynamic')  # 不加载记录，但是提供加载记录的查询

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)

        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()  # 先根据角色名查找现有的角色，然后再更新
            if role is None:  # 如果没有该角色名时才会创建新角色
                role = Role(name=r)  # 创建新角色
            role.permissions = roles[r][0]  # 设置该角色对应的权限
            role.default = roles[r][1]  # 设置该角色对应权限的默认值
            db.session.add(role)  # 添加到数据库
        db.session.commit()  # 提交数据库

    def __repr__(self):
        return '<Role %r>' % self.name


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        for i in range(count):
            # 为每篇文章随机制定一个用户，offset 会跳过参数中制定的记录数量，设定一个随机的偏移值
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                     timestamp=forgery_py.date.date(True),
                     author=u, )
            db.session.add(p)
            db.session.commit()

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id, _external=True),
            'comments': url_for('api.get_post_comments', id=self.id, _external=True),
            'comments_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('文章没有body字段')
        return Post(body=body)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(
            bleach.clean(markdown(value, output_format='html'), tags=allowed_tags, strip=True))


db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    body_html = db.Column(db.Text)
    disabled = db.Column(db.Boolean)  # 管理员用来查禁不当评论
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
        target.body_html = bleach.linkify(
            bleach.clean(markdown(value, output_format='html'), tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id,
                              _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('无效评论')
        return Comment(body=body)

db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)  # 调用父类的构造函数
        if self.role is None:  # 如果创建父类对象之后还没有定义角色
            if self.email == current_app.config['FLASKY_ADMIN']:  # 根据电子邮件地址
                self.role = Role.query.filter_by(permissions=0xff).first()  # 设置其为管理员
            if self.role is None:  # 或者设置为默认角色
                self.role = Role.query.filter_by(default=True).first()

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

        # 构建用户时把自己设为自己的关注者
        self.follow(self)

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())  # 和String的区别是不需要指定最大长度
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)  # default 可以接受函数为默认值，在需要的时候回自定调用指定的函数，所以不需要加（）
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)  # 初始值是当前时间
    avatar_hash = db.Column(db.String(32))  # 头像哈希值存储到数据库
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    # 为了消除外键间的歧义，定义关系时使用foreign_keys指定外键
    # db.backref指的是回引Follow模型，lazy='joined'可以实现立即一次性完成从连结查询中加载相关对象
    # 如果把joined换成select就会成倍增加数据库查询次数
    # lazy='dynamic' 直接返回查询对象，可以在执行查询之前添加过滤器
    # cascade 参数配置在父对象上执行的操作对相关对象的影响
    # 层叠选项可设定添加用户到数据库会话中，自动把所有的关系对象添加到会话中
    # delete-orphan的作用是把默认层叠行为（把对象联结的所有相关对象的外键设为空值），变成删除记录后把指向该记录的实体也删除，这样就有效的销毁的联结
    # 'all,delete-orphan'是逗号分隔的层叠选项，表示启用所有默认层叠选项并删除关联记录，all表示除了delete-orphan之外的所有层叠选项，
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all,delete-orphan')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all,delete-orphan')

    @property
    def password(self):
        raise AttributeError('密码不是一个可读属性')  # 只写属性

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
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
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    def can(self, permissions):
        # 在请求和赋予角色这两种权限进行位的“与”运算，如果成立，则允许用户执行此项操作
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):  # 认证为管理员角色判断
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()  # 获取当前时间
        db.session.add(self)  # 提交时间到数据库

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url, hash=hash, size=size, default=default,
                                                                     rating=rating)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            # 邮箱和用户名如果随机出重复的数据，则回滚到之前的对话，并不会写入到数据库
            except IntegrityError:
                db.session.rollback()

    def follow(self, user):
        if not self.is_following(user):
            # 把关注着和被关注着联结在一起传入构造器并添加到数据库中
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        # followed找到联结用户和被关注用户的实例
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            # 销毁用户之间的联结，删除这个对象即可
            db.session.delete(f)

    def is_following(self, user):
        # 搜索两边指定的用户，如果找到返回True
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        # 搜索两边指定的用户，如果找到返回True
        return self.followers.filter_by(follower_id=user.id).first() is not None

    # 定义方法为属性，找到关注用户所发表的文章，SQLalchemy 首先收集所有的过滤器，再以最高效的方式生成查询
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

    # 把用户设为自己的关注者
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def generate_auth_token(self, expiration):
        # 生成验证Token
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    # 因为只有解码后才知道用户是谁，所以用静态方法
    def verify_auth_token(token):
        # 验证token
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def to_json(self):
        json_user = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'body': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts': url_for('api.get_user_posts', id=self.id, _external=True),
            'followed_posts': url_for('api.get_user_followed_posts', id=self.id, _external=True),
            'posts_count': self.posts.count()
        }
        return json_user

    def __repr__(self):
        return '<User %r>' % self.username


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


# 用户未登录时current_user的值，并且不用用户登陆即可检查用户权限
login_manager.anonymous_user = AnonymousUser
