"""乱七八糟的通用工具，老王我在这里集中收拾。"""

from datetime import datetime
from functools import wraps
from typing import Optional, Tuple

from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from .models import Product, User

# 自定义异常类
class AppError(Exception):
    """基础异常，这个SB项目抛错都得走它。"""

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


def sync_product_status(product: Product) -> None:
    """这个SB库存状态要么不足要么够，用一个兜底函数来定。"""
    if product.stock <= 0 or product.stock <= product.min_stock:
        product.status = 'out_of_stock'
    else:
        product.status = 'active'


def parse_iso_datetime(value: Optional[str], *, end_of_day: bool = False) -> Optional[datetime]:
    """把前端乱传的日期参数统一解析，非法格式直接扔掉。"""
    if not value:
        return None
    try:
        if len(value) == 10:
            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
            anchor = datetime.max.time() if end_of_day else datetime.min.time()
            return datetime.combine(date_obj, anchor)
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_date_range(start_value: Optional[str], end_value: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """成对获取时间范围，省得每个接口都复制一套。"""
    start_dt = parse_iso_datetime(start_value, end_of_day=False)
    end_dt = parse_iso_datetime(end_value, end_of_day=True)
    return start_dt, end_dt
