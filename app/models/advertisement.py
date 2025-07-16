# models/advertisement.py
from flask_sqlalchemy import SQLAlchemy
from datetime import  datetime,timezone
from app.extensions import db

class Advertisement(db.Model):
    __tablename__  = 'advertisement'
    ad_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # 广告名称
    description = db.Column(db.String(255), nullable=True)  # 广告描述
    duration= db.Column(db.Integer, nullable=False)
    video_url = db.Column(db.String(255), nullable=False)  # 广告视频 URL
    reward = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # 是否启用广告
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间

