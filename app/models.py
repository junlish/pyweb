from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import  TimedJSONWebSignatureSerializer as TSerializer
from app import db, login_manager
from app.exceptions import ValidationError
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app, url_for
from markdown import markdown
import bleach

class Role(db.Model):
    __tablename__='roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role {}>'.format(self.name)

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES |
                Permission.MODERATE_COMMENTS, True),
            'Administrator': (0xff, False)
        }
        for r in roles:
            permissions, df = roles[r]
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.default = df
            role.permissions = permissions
            db.session.add(role)
        db.session.commit()


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS  = 0x08
    ADMINISTER = 0x80


class Follow(db.Model):
    __tablename__='follows'
    follower_id=db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id=db.Column(db.Integer,db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default= datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True,index=True)
    # role_id are foreign key in roles table's id column
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default= False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(128))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id], backref=db.backref('follower', lazy='joined')
                               , lazy='dynamic', cascade='all,delete-orphan')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], backref=db.backref('followed',lazy='joined')
                                , lazy='dynamic',cascade='all,delete-orphan')
    comments = db.relationship('Comment', backref='author',lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(default = True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=2600):
        s = TSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = TSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirm') != self.id:
            return False
        self.confirm(True)
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = TSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    @classmethod
    def reset_password(cls, token, password):
        s = TSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False, "Invalid token"

        user_id = data.get('reset')
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return False, "Invalid token - wrong user"
        else:
            user.password = password
            return True, user

    def generate_change_email_token(self, new_email, expiration=3600):
        s = TSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'user_id': self.id, 'email': new_email})

    @classmethod
    def change_email(cls, token):
        s = TSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False, "Invalid token"

        user_id = data.get('user_id')
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return False, "Invalid token - wrong user"
        else:
            user.email = data.get('email')
            return True, user

    def can(self, permission):
        return self.role is not None and self.role.permissions & permission == permission

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(followed=user)
            self.followed.append(f)

    def unfollow(self, user):
        if user.id is None:
            return False
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            self.followed.remove(f)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

    @staticmethod
    def verify_auth_token(token):
        s = TSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def generate_auth_token(self, expiration):
        s = TSerializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id,_external=True),
            'username' : self.username,
            'member_since' : self.member_since,
            'last_seen' : self.last_seen,
            'posts': url_for('api.get_user_posts',id=self.id, _external=True),
            'followed_posts': url_for('api.get_user_followed_posts', id=self.id, _external=True),
            'post_count':self.posts.count()
        }
        return json_user

    def __repr__(self):
        return '<User {}>'.format(self.username)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class AnonymousUser(AnonymousUserMixin):
    def can(self, permission):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @staticmethod
    def on_changed_body(target, value ,oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                    'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                    'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_post = {
            'url' : url_for('api.get_post',id=self.id, _external= True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp' : self.timestamp,
            'author': url_for('api.get_user', id=self.author_id, _external= True),
            'comments' : url_for('api.get_post_comments', id=self.id, _external=True),
            'comment_count' : self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError("Post does not have a body")
        return Post(body=body)

db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    __tablename__='comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    disabled = db.Column(db.Boolean, default=False)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code',
                        'em', 'i', 'strong']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                       tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.author_id, _external=True),
            'post': url_for('api.get_post', id=self.post_id, _external=True),
            'disabled' : self.disabled
        }
        return json_comment

db.event.listen(Comment.body, 'set', Comment.on_changed_body)
