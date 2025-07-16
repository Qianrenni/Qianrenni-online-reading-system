import json
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

def admin_required(fn):
    """
    自定义修饰器：验证用户是否具有管理员权限。
    必须与 @jwt_required() 一起使用。
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # 获取当前用户的 JWT 身份信息
        access_user = json.loads(get_jwt_identity())
        if not access_user or access_user['role'] != 'admin':
            return jsonify({'error': 'no right identity'}), 403  # 403 表示禁止访问
        return fn(*args, **kwargs)
    return wrapper