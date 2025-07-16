# models/user.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from app.extensions import db

# models/payment_history.py
class PaymentHistory(db.Model):
    payment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,nullable=False)
    book_id = db.Column(db.Integer,nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_time = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间

    def to_dict(self):
        return {
            'payment_id': self.payment_id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'amount': self.amount,
            'payment_time': self.payment_time,
            'created_at': self.created_at
        }
