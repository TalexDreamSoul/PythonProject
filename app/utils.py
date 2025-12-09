from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import g, jsonify
from .models import User

# 自定义异常类
class AppError(Exception):
    def __init__(self, message, code=400, data=None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)

class ForbiddenError(AppError):
    def __init__(self, message="Permission denied"):
        super().__init__(message, 403)

class NotFoundError(AppError):
    def __init__(self, message="Resource not found"):
        super().__init__(message, 404)

class ValidationError(AppError):
    def __init__(self, message="Validation error"):
        super().__init__(message, 400)

# 统一返回格式
class Response:
    @staticmethod
    def success(data=None):
        """成功返回格式"""
        return jsonify({
            "code": 0,
            "message": "success",
            "data": data
        }), 200
    
    @staticmethod
    def error(code, message, data=None):
        """错误返回格式"""
        return jsonify({
            "code": code,
            "message": message,
            "data": data
        }), code
    
    @staticmethod
    def pagination(items, total, page, size):
        """分页返回格式"""
        return jsonify({
            "code": 0,
            "message": "success",
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "size": size
            }
        }), 200

# 角色权限装饰器
def role_required(roles):
    if isinstance(roles, str):
        allowed = {roles}
    else:
        allowed = set(roles)
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            identity = get_jwt_identity()
            user = User.query.filter_by(username=identity).first()
            if not user:
                raise NotFoundError("User not found")
            if user.role not in allowed:
                raise ForbiddenError()
            g.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator