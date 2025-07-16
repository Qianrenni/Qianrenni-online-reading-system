# models/user.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

from app.extensions import db

class User(db.Model):
    __tablename__  = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('user', 'admin', name='role_enum'), nullable=False)
    balance = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, default=1, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间
    updated_at =db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间
