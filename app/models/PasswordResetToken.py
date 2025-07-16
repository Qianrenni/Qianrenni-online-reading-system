from datetime import datetime, timezone
from app.extensions import db


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    token = db.Column(db.String(256), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间
    expired_at = db.Column(db.DateTime, nullable=False)
    user = db.relationship('User', backref='password_reset_tokens')
