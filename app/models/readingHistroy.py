# models/user.py
from datetime import datetime, timezone
from app.extensions import db


class ReadingHistory(db.Model):
    __tablename__ = 'reading_history'


    reading_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    progress = db.Column(db.Numeric(5, 2), nullable=False, default=0.00)
    last_read_page = db.Column(db.Integer, nullable=True, default=0)
    reading_device = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间
