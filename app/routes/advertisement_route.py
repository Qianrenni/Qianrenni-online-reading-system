from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

import app.utils.payparms
from app.extensions import db
from app.models.advertisement import Advertisement
from app.models.user import User
from app.models.userAdvertisement import UserAdvertisement

advertisement_bp= Blueprint('ad', __name__)

@advertisement_bp.route('/watch_ad/<int:user_id>', methods=['GET'])
def watch_ad(user_id):
    """模拟广告观看"""
    # 获取当前日期
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # 查询用户当日的广告观看记录
    user_ads_today = UserAdvertisement.query.filter(
        UserAdvertisement.user_id == user_id,
        UserAdvertisement.created_at >= today_start,
        UserAdvertisement.created_at < today_end
    ).all()

    # 如果用户已经观看了 3 条广告，直接返回提示
    if len(user_ads_today) >= 3:
        return jsonify({"message": "You have already watched 3 ads today.", "status": "limit_reached"}), 403

    # 查询一条随机的有效广告
    random_ad = Advertisement.query.filter_by(is_active=True).order_by(db.func.random()).first()

    # 如果没有可用广告，返回错误响应
    if not random_ad:
        return jsonify({"message": "No active ads available.", "status": "no_ads"}), 404

    # 插入一条新的观看记录
    new_record = UserAdvertisement(
        ad_id=random_ad.ad_id,
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    db.session.add(new_record)
    db.session.commit()

    # 返回广告信息
    return jsonify({
        "message": "Here is your ad.",
        "status": "success",
        "ad": {
            "ad_id": random_ad.ad_id,
            # "name": random_ad.name,
            # "description": random_ad.description,
            "video_url": f"{app.utils.payparms.serverUrl}/static/{random_ad.video_url}",
            "reward": float(random_ad.reward)  # 确保数值类型兼容 JSON
        }
    }), 200



@advertisement_bp.route('/give_reward', methods=['POST'])
def give_reward():
    """发放书币奖励"""
    # 从请求中获取参数
    user_id = request.json.get('user_id')
    ad_id = request.json.get('ad_id')

    # 查询广告记录
    ad = Advertisement.query.get(ad_id)
    if not ad:
        return jsonify({'status': 'failed', 'message': '广告不存在'}), 404

    # 查询用户广告观看记录（未领取奖励）
    user_ad = UserAdvertisement.query.filter_by(ad_id=ad_id, user_id=user_id, isRewarded=False).first()
    if not user_ad:
        return jsonify({'status': 'failed', 'message': '未找到符合条件的观看记录或奖励已领取'}), 400

    # 查询用户记录
    user = User.query.get(user_id)
    if not user:
        return jsonify({'status': 'failed', 'message': '用户不存在'}), 404

    try:
        # 给用户增加书币奖励
        user.balance += ad.reward
        user_ad.isRewarded = True  # 标记为已领取奖励
        db.session.commit()

        # 返回成功响应
        return jsonify({
            'status': 'success',
            'message': f'奖励已发放! 你获得了 {ad.reward} 书币',
            'balance': float(user.balance)  # 确保数值类型兼容 JSON
        }), 200

    except Exception as e:
        # 如果发生异常，回滚事务并返回错误信息
        db.session.rollback()
        return jsonify({'status': 'failed', 'message': f'发放奖励失败: {str(e)}'}), 500
