from functools import wraps
from flask import g
from .errors import forbidden


def permission_required(permission):
    def decorator(func):
        @wraps(func)    # copy attributes of func to decorated_func
        def decorated_func(*args, **kwargs):
            if g.current_user.can(permission):
                return func(*args, **kwargs)
            else:
                return forbidden('Insufficient permissions')
        return decorated_func
    return decorator
