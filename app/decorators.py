from functools import wraps
from flask import abort
from flask_login import current_user
from app.models import Permission


def permission_required(permission):
    def decorator(func):
        @wraps(func)    # copy attributes of func to decorated_func
        def decorated_func(*args, **kwargs):
            if current_user.can(permission):
                return func(*args, **kwargs)
            else:
                abort(403)
        return decorated_func
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)
