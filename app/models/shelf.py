# models/user.py
from datetime import datetime, timezone
from app.extensions import db


class Shelf(db.Model):
    __tablename__ = 'shelf'

    shelf_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间
