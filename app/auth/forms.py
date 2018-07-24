from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email,Length, Regexp, EqualTo
from app.models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('用户名', validators=[DataRequired(), Length(1,64), \
            Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0, 'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('密码', validators=[DataRequired(), EqualTo('password2', message='两次输入密码必须一致')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValueError('邮箱已注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValueError('用户名已注册')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('当前密码', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired(), EqualTo('password2', message='两次输入密码必须一致')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('修改密码')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64), \
                                              Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                     'Usernames must have only letters, numbers, dots or underscores')])
    submit = SubmitField('重置密码')

class PasswordResetForm(FlaskForm):
    password = PasswordField('密码', validators=[DataRequired(), EqualTo('password2', message='两次输入密码必须一致')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('重置密码')