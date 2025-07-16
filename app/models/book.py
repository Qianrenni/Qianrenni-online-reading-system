# models/user.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

from app.extensions import db

# models/book.py
class Book(db.Model):
    __tablename__ = 'books'
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)
    store_path=db.Column(db.String(255), nullable=False)
    is_paid = db.Column(db.Boolean, nullable=False, default=False)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    free_pages = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(255), nullable=True)
    total_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间
