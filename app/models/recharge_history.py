# models/user.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from app.extensions import db

# models/recharge_history.py
class RechargeHistory(db.Model):
    recharge_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.Enum('pending', 'success', 'failed', name='payment_status_enum'), nullable=False)
    payment_method = db.Column(db.Enum('alipay', 'wechat', 'credit', name='payment_method_enum'), nullable=False)
    recharge_time = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间


    def to_dict(self):
        """将 RechargeHistory 实例转换为字典"""
        return {
            'recharge_id': self.recharge_id,
            'user_id': self.user_id,
            'amount': str(self.amount),  # 转换为字符串，避免 JSON 格式不支持 Decimal
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'recharge_time': self.recharge_time.isoformat() if self.recharge_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }