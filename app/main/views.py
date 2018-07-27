from datetime import datetime
from flask import render_template, session, redirect, url_for, abort, flash, request,current_app
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User, Role
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm
from app.decorators import admin_required
from app.models import Permission, Post, User



@main.route('/',methods=['GET','POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))

    page = request.args.get('page',1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page,
                per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('index.html', form = form, posts=posts, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username= username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


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


@main.route('/user/edit-profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.confirmed = form.confirmed.data
        user.name = form.name.data
        user.about_me = form.about_me.data
        user.location = form.location.data
        user.role = Role.query.get(form.role.data)
        db.session.add(user)
        flash('用户信息更新完成')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    return render_template('edit-profile.html', form=form, user=user)


@main.route('/post/<int:id>')
def post(id):
    p = Post.query.get_or_404(id)
    return render_template('post.html', posts=[p])
