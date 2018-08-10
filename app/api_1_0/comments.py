from flask import request,g, jsonify, url_for
from . import api
from app.models import Post, Permission, Comment
from app import db
from app.auth import auth
from .decorators import permission_required


@api.route('/comments/<int:id>')
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify({'comment': comment.to_json()})


@api.route('/comments/')
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page,
            per_page=current_app.config[ 'FLASKY_COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    prev_page = None
    if pagination.has_prev:
        prev_page = url_for('api.get_comments', page=page - 1, _external=True)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_comments', page=page + 1, _external=True)
    return jsonify({
        'comments':[ comment.to_json() for comment in comments],
        'prev': prev_page,
        'next': next_page,
        'count': pagination.total
    })
