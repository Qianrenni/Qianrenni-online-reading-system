import datetime
import hashlib
import json
import time

from flask_jwt_extended import jwt_required, get_jwt_identity

import app.utils.payparms
from app.services.auth_service import register_user, login_user, add_balance, deduct_balance, get_balance_route
from app.extensions import mail
from flask import Blueprint, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.user import User
from app.models.PasswordResetToken import PasswordResetToken
from flask_mail import Message
import os
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    return register_user(data)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    return login_user(data)
@auth_bp.route('/autoLogin', methods=['POST'])
def autoLogin():
    pass
# 新增：增加余额接口
@auth_bp.route('/add_balance', methods=['POST'])
def add_balance_route():
    # user_id = get_jwt_identity()  # 获取当前登录用户的user_id
    data = request.get_json()
    amount = data.get('amount')

    user_id = data.get('userId')
    
    if amount is None:
        return jsonify({"error": "Amount is required"}), 400
    
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"error": "Invalid amount format"}), 400
    
    return add_balance(user_id, amount)

# 新增：扣除余额接口
@auth_bp.route('/deduct_balance', methods=['POST'])
# @jwt_required()  # 确保用户已经登录并携带JWT token
def deduct_balance_route():
    # user_id = get_jwt_identity()  # 获取当前登录用户的user_id
    data = request.get_json()
    amount = data.get('amount')

    user_id = data.get('userId')
    if amount is None:
        return jsonify({"error": "Amount is required"}), 400
    
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"error": "Invalid amount format"}), 400
    
    return deduct_balance(user_id, amount)

# 新增：获取余额接口
@auth_bp.route('/get_balance', methods=['POST'])
# @jwt_required()  # 确保用户已经登录并携带JWT token
def get_balance():
    data = request.get_json()
    user_id = data.get('userId')
    return get_balance_route(user_id)
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')

    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"status": "error", "message": "Email not found"}), 404

    # 生成重置密码令牌
    token = generate_reset_token(user.user_id)  # ✅ 使用正确的字段名 user_id
    reset_link = f"{app.utils.payparms.serverUrl}/auth/reset-password/{token}"

    # 发送邮件
    msg = Message("Password Reset Request", recipients=[email])
    msg.body = f"To reset your password, please click the following link: {reset_link}"
    try:
        mail.send(msg)
        return jsonify({"status": "success", "message": "Password reset link has been sent to your email"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to send email: {str(e)}"}), 500


def generate_reset_token(user_id):
    salt = os.urandom(16).hex()
    token = hashlib.sha256(f"{user_id}{salt}{time.time()}".encode()).hexdigest()
    expired_at =  datetime.datetime.utcnow() + datetime.timedelta(minutes=5)  # 令牌过期时间为1小时
    # 将令牌存储到数据库
    reset_token = PasswordResetToken(user_id=user_id, token=token, expired_at=expired_at)
    db.session.add(reset_token)
    db.session.commit()

    return token


# 重置密码
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'GET':
        # 验证 token 是否有效
        user_id = verify_reset_token(token)
        if not user_id:
            return "Invalid or expired token", 400

        # 返回重置密码页面
        return render_template('reset_password.html', token=token)

    elif request.method == 'POST':
        # 处理密码重置逻辑
        new_password = request.form.get('password')
        if not new_password:
            return jsonify({"status": "error", "message": "New password is required"}), 400

        # 验证令牌
        user_id = verify_reset_token(token)
        if not user_id:
            return jsonify({"status": "error", "message": "Invalid or expired token"}), 400

        # 获取用户并更新密码
        user = User.query.get_or_404(user_id)
        hashed_password = generate_password_hash(new_password)
        user.password = hashed_password
        db.session.commit()

        return jsonify({"status": "success", "message": "Password has been reset successfully"}), 200
def verify_reset_token(token):
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    if not reset_token or reset_token.expired_at <  datetime.datetime.utcnow():
        return None
    return reset_token.user_id
@auth_bp.route('/changepassword', methods=['POST'])
@jwt_required()  # 确保请求包含有效的 JWT
def change_password():

    user_id = json.loads(get_jwt_identity())['userid']  # 自动提取用户 ID
    # 获取旧密码和新密码
    old_password = request.json.get('oldPassword')
    new_password = request.json.get('newPassword')
    if not old_password or not new_password:
        return jsonify({"status": "error", "message": "All fields are required"}), 400
    # 查询用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # 验证旧密码是否正确
    if not check_password_hash(user.password, old_password):
        return jsonify({"status": "error", "message": "Old password is incorrect"}), 400
    # 更新密码
    hashed_new_password = generate_password_hash(new_password)
    user.password = hashed_new_password
    db.session.commit()
    return jsonify({"status": "success", "message": "Password has been updated successfully"}), 200
@auth_bp.route('/updateusername', methods=['POST'])
@jwt_required()
def update_username():

    try:
        user_id = json.loads(get_jwt_identity())['userid']
        username = request.json.get('username')
        user = User.query.get(user_id)
        user.username = username
        db.session.commit()
        return jsonify({"status": "success", "message": "Username has been updated successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
