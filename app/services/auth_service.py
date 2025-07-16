import json

from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.user import User
from flask_jwt_extended import create_access_token
from decimal import Decimal

def register_user(data):
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400
    
    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        balance = 0,
        role='user',  # 赋默认值 'user'
        is_active=True
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully"}), 201

def login_user(data):
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401
    if not user.is_active:
        return jsonify({"error": "User is not active"}), 401
    access_token = create_access_token(identity=json.dumps({"userid": str(user.user_id),"role":user.role}))
    return jsonify({"access_token": access_token,"username":user.username,"balance":user.balance,"userId":user.user_id}), 200


# 新增：增加余额
def add_balance(user_id, amount):
    # 将 amount 转换为 float 类型，确保类型一致
    amount = Decimal(amount)
    if amount <= 0:
        return jsonify({"error": "Amount to add must be positive"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.balance += amount
    db.session.commit()
    
    return jsonify({"message": f"Balance increased by {amount}", "new_balance": user.balance}), 200

# 新增：扣除余额
def deduct_balance(user_id, amount):
    # 将 amount 转换为 float 类型，确保类型一致
    amount = Decimal(amount)
    if amount <= 0:
        return jsonify({"error": "Amount to deduct must be positive"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if user.balance < amount:
        return jsonify({"error": "Insufficient balance"}), 400
    
    user.balance -= amount
    db.session.commit()
    
    return jsonify({"message": f"Balance deducted by {amount}", "new_balance": user.balance}), 200

def get_balance_route(user_id):
    # user_id = get_jwt_identity()  # 获取当前登录用户的user_id

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({"balance": user.balance}), 200