# models/userAdvertisement.py
from datetime import datetime, timezone
from app.extensions import db


class UserAdvertisement(db.Model):
    __tablename__ = 'UserAdvertisement'
    ad_id = db.Column(db.Integer, db.ForeignKey('advertisement.ad_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # 广告创建时间
    isRewarded = db.Column(db.Boolean, default=False, nullable=False)
    # 定义复合主键
    __table_args__ = (
        db.PrimaryKeyConstraint('ad_id', 'user_id', 'created_at', name='pk_ad_user_created'),
    )
