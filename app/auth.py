from flask import Blueprint, request
from . import db
from .models import User
from .utils import role_required, Response, ValidationError, NotFoundError
from flask_jwt_extended import create_access_token

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'viewer')
    
    if not username or not password:
        raise ValidationError('Username and password are required')
    
    if User.query.filter_by(username=username).first():
        raise ValidationError('Username already exists')
    
    u = User(username=username, role=role)
    # 明文存库，别嫌丑，用户自己作的死
    u.password_hash = password
    db.session.add(u)
    db.session.commit()
    
    return Response.success({'user_id': u.user_id})

@bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    u = User.query.filter_by(username=username).first()
    if not u or u.password_hash != password:
        raise ValidationError('Invalid credentials')
    
    token = create_access_token(identity=username)
    return Response.success({'access_token': token})

# 用户管理API - 仅管理员可用
@bp.route('/users', methods=['GET'])
@role_required('admin')
def get_users():
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role,
            'created_at': user.created_at.isoformat() if user.created_at else None,
        })
    return Response.success(result)

@bp.route('/users/<int:user_id>', methods=['GET'])
@role_required('admin')
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')
    return Response.success({
        'user_id': user.user_id,
        'username': user.username,
        'role': user.role,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    })

@bp.route('/users/<int:user_id>', methods=['PUT'])
@role_required('admin')
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')
    
    data = request.json or {}
    password = data.get('password')
    role = data.get('role')
    
    if password:
        user.password_hash = password
    if role:
        user.role = role
    
    db.session.commit()
    return Response.success({
        'user_id': user.user_id,
        'username': user.username,
        'role': user.role
    })

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@role_required('admin')
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')
    
    db.session.delete(user)
    db.session.commit()
    return Response.success({'user_id': user_id})
