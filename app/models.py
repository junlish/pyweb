
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import  TimedJSONWebSignatureSerializer as TSerializer
from app import db, login_manager
from flask_login import UserMixin
from flask import current_app

class Role(db.Model):
    __tablename__='roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role {}>'.format(self.name)



class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True,index=True)
    # role_id are foreign key in roles table's id column
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default= False)

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


    def __repr__(self):
        return '<User {}>'.format(self.username)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
