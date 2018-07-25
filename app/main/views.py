from datetime import datetime
from flask import render_template, session, redirect, url_for, abort, flash
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User
from . import main
from .forms import EditProfileForm



@main.route('/',methods=['GET','POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        return redirect(url_for('.index'))
    return render_template('index.html', form=form, name=session.get('name'), known=session.get('known',False),
                           current_time= datetime.now())


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username= username).first()
    if user is None:
        abort(404)
    return render_template('user.html', user = user)


@main.route('/user/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.about_me = form.about_me.data
        current_user.location = form.location.data
        db.session.add(current_user)
        flash('用户资料已更新')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit-profile.html', form=form)

