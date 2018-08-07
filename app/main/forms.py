from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email,Regexp
from flask_pagedown.fields import PageDownField

from app.models import Role, User


class EditProfileForm(FlaskForm):
    name = StringField('真实姓名', validators=[Length(0,64)])
    location = StringField('地域', validators=[Length(0,64)])
    about_me = TextAreaField('自我介绍')
    submit = SubmitField('提交')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[ DataRequired(), Length(1,64), Email()])

    username = StringField('用户名', validators=[DataRequired(), Length(1, 64), \
                                              Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                     'Usernames must have only letters, numbers, dots or underscores')])
    confirmed = BooleanField('邮箱已确认')
    role = SelectField('用户角色', coerce=int)
    name = StringField('真实姓名', validators=[Length(0,64)])
    location = StringField('地域', validators=[Length(0, 64)])
    about_me = TextAreaField('自我介绍')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all() ]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValueError('邮箱已注册')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValueError('用户名已注册')


class PostForm(FlaskForm):
    body = PageDownField("发布内容", validators=[DataRequired()])
    submit = SubmitField("提交")


class CommentForm(FlaskForm):
    body = PageDownField("", validators=[DataRequired()])
    submit = SubmitField("提交")