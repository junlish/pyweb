from datetime import datetime
from flask import render_template, session, redirect, url_for, abort, flash, request,current_app, make_response
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User, Role, Comment
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from app.decorators import admin_required, permission_required
from app.models import Permission, Post, User



@main.route('/',methods=['GET','POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))

    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed',''))

    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query

    page = request.args.get('page',1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(page,
                per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('index.html', form = form, posts=posts, pagination=pagination, show_followed=show_followed)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '',max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1',max_age=30*24*60*60)
    return resp


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


@main.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
    p = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=p, author=current_user._get_current_object())
        db.session.add(comment)
        flash("评论已添加")
        return redirect(url_for('.post', id=p.id, page=-1))

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE']
    if page==-1:
        #calcuate last page
        page = (p.comments.count() -1)/ per_page + 1
    pagination = p.comments.order_by(Comment.timestamp.asc()).paginate(page, per_page=per_page , error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[p],form=form, comments=comments, pagination=pagination)


@main.route('/edit-post/<int:id>',methods=['GET','POST'])
def edit_post(id):
    p = Post.query.get_or_404(id)
    if  current_user!=p.author and not current_user.is_administrator():
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        p.body = form.body.data
        db.session.add(p)
        flash("Post已修改")
        return redirect(url_for('.post',id=id))
    form.body.data = p.body
    return render_template('edit_post.html', form= form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("关注的用户不存在:{}".format(username))
        return redirect(url_for(".index"))
    if current_user.is_following(user):
        flash("你早已关注该用户")
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash("关注用户{}成功".format(username))
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("关注的用户不存在:{}".format(username))
        return redirect(url_for(".index"))
    if current_user.is_following(user):
        current_user.unfollow(user)
        flash("取消关注{}成功".format(username))
        return redirect(url_for('.user', username=username))
    else:
        flash("您并未关注{},无法操作".format(username))
        return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("用户不存在:{}".format(username))
        return redirect(url_for(".index"))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'] ,
                                         error_out=False)
    follows = [  {'user':item.follower, 'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of ", endpoint='.followers',
                           pagination= pagination, follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("用户不存在:{}".format(username))
        return redirect(url_for(".index"))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                                         error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by ", endpoint='.followed_by',
                           pagination=pagination, follows=follows)

