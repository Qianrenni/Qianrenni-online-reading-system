import logging

from flask import Blueprint, request, jsonify
from app.services.recharge_service import create_alipay_order, handle_alipay_notification, create_order, \
    get_recharge_history

recharge_route = Blueprint('recharge_route', __name__)


@recharge_route.route('/add', methods=['POST'])
def recharge():
    try:
        data = request.json
        user_id = data.get('userId')
        amount = data.get('amount')

        if not user_id or not amount or float(amount) <= 0:
            return jsonify({"error": "Invalid parameters", "user_id": user_id, "amount": amount}), 400

        result = create_order(user_id, amount)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recharge_route.route('/get', methods=['GET'])
def get_history():
    try:
        user_id = request.args.get('userId')
        if not user_id:
            return jsonify({"error": "Invalid parameters"}), 400

        recharges = get_recharge_history(user_id)
        return recharges, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 支付宝支付这部分还没写完，先用上面的接口
@recharge_route.route('/api/recharge', methods=['POST'])
def create_recharge():
    """
    创建充值订单并返回跳转支付宝的链接
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        amount = data.get('amount')

        if not user_id or not amount or float(amount) <= 0:
            return jsonify({"error": "Invalid parameters", "user_id": user_id, "amount": amount}), 400

        result = create_alipay_order(user_id, amount)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@recharge_route.route('/api/notify', methods=['POST'])
def alipay_notify():
    """
    支付宝异步通知处理
    """
    try:
        data = request.form.to_dict()
        result = handle_alipay_notification(data)

        if result:
            return "success", 200
        else:
            return "failure", 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
