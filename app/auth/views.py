from flask import render_template, redirect, url_for, request,flash
from flask_login import login_user, logout_user, login_required, current_user

from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm,ChangeEmailRequestForm
from app.models import User
from app import db
from app.email_util import send_email


@auth.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    flash('您已登出。')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username = form.username.data, password= form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, tocken=token)

        flash('用户创建成功， 账户确认邮件已发送。')
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('邮箱已确认')
    else:
        flash('确认邮件的链接无效或已过期')
    return redirect(url_for('main.index'))


@auth.route('/reconfirm')
@login_required
def resend_confirm():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token)

    flash(' 账户确认邮件已发送。')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for("main.index"))
    return render_template('auth/unconfirmed.html')


@auth.route('/change_password', methods=['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.current_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('密码已修改')
            return redirect(url_for('main.index'))
        else:
            flash('当前密码错误')
            return render_template('auth/change_password.html', form=form)
    return  render_template('auth/change_password.html', form=form)

@auth.route('/reset_password_request', methods=['GET','POST'])
def reset_password_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        # check user/email exists
        user = User.query.filter_by(username = form.username.data, email= form.email.data).first()
        if user is None:
            flash('用户名或email地址错误')
            return render_template('auth/reset_password_request.html', form=form)
        else:
            # send reset email
            token = user.generate_reset_token()
            send_email(user.email, '密码重置', 'auth/email/reset', user=user, token=token)
            flash(' 账户密码重置邮件已发送至{}。'.format(user.email))
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/confirm_reset_password/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        op_status, ret_obj = User.reset_password(token, form.password.data)
        if op_status:
            db.session.add(ret_obj)
            db.session.commit()
            flash('密码已重置.')
            return redirect(url_for('auth.login'))
        else:
            flash(ret_obj)
            return render_template('auth/reset_password.html', form=form)
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change_email_request', methods=['GET','POST'])
@login_required
def change_email_request():
    form = ChangeEmailRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id= current_user.id).first()
        token = user.generate_change_email_token(form.email.data)
        send_email(form.email.data, '修改email地址', 'auth/email/change_email', user=user, token=token)
        flash(' 账户邮件地址修改已发送至{}。'.format(form.email.data))
        return redirect(url_for('auth.login'))
    return render_template('auth/change_email.html', form=form)


@auth.route('/change_email/<token>')
def change_email(token):
    op_status, ret_obj = User.change_email(token)
    if op_status:
        db.session.add(ret_obj)
        db.session.commit()
        flash('Email已修改.')
    else:
        flash('Email修改失败:{}.'.format(ret_obj))
    return redirect(url_for('auth.login'))