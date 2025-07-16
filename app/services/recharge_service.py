from alipay import AliPay
from app.utils.payparms import *
from app.models.recharge_history import RechargeHistory
from app.models.user import User
import os
from datetime import datetime
from app.extensions import db
from flask import jsonify
from app.services.auth_service import add_balance,deduct_balance

def create_order(user_id, amount):
    try:
        new_recharge = RechargeHistory(
            user_id=user_id,
            amount=amount,
            payment_status='pending',
            payment_method='alipay',
        )
        add_balance(user_id,amount)
        db.session.add(new_recharge)
        db.session.commit()
        return {"message": "Order created successfully", "recharge_id": new_recharge.recharge_id}
    except Exception as e:
        db.session.rollback()
        raise e
    
def get_recharge_history(user_id):
    recharges = RechargeHistory.query.filter_by(user_id=user_id).all()
        # 将每个充值记录转换为字典，然后返回 JSON 响应
    recharge_list = [recharge.to_dict() for recharge in recharges]
    return jsonify(recharge_list)


def create_alipay_order(user_id, amount):
    """
    创建支付宝充值订单
    """

    try:
        # 加载支付宝配置
        alipay = AliPay(
            appid=appid,
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=True,
        )


        # 创建订单
        recharge_id = int(datetime.utcnow().timestamp())
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=recharge_id,
            total_amount=str(amount),
            subject="书币充值",
            notify_url=notify_url,
            return_url=return_url
        )

        # 保存订单记录到数据库
        new_recharge = RechargeHistory(
            recharge_id=recharge_id,
            user_id=user_id,
            amount=amount,
            payment_status='pending',
            payment_method='alipay',
        )
        db.session.add(new_recharge)
        db.session.commit()

        redirect_url = f"https://openapi-sandbox.dl.alipaydev.com/gateway.do?{order_string}"
        return {"message": "Redirect to Alipay for payment", "recharge_id": recharge_id, "redirect_url": redirect_url}

    except Exception as e:
        db.session.rollback()
        raise e


def handle_alipay_notification(data):
    """
    处理支付宝异步通知
    """
    try:
        # 加载支付宝配置
        alipay = AliPay(
            appid=appid,
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=True,
        )

        # 验证签名
        sign = data.pop("sign", None)
        if not alipay.verify(data, sign):
            return False

        # 更新充值记录状态
        out_trade_no = data.get("out_trade_no")
        trade_status = data.get("trade_status")

        recharge = RechargeHistory.query.filter_by(recharge_id=out_trade_no).first()
        if not recharge:
            return False

        if trade_status == "TRADE_SUCCESS":
            recharge.payment_status = "success"
            user = User.query.get(recharge.user_id)
            user.balance += recharge.amount*10
            recharge_history=RechargeHistory.query.get(out_trade_no)
            recharge_history.payment_status="success"
            db.session.commit()
            return True
        elif trade_status == "TRADE_FAILED":
            recharge.payment_status = "failed"
            db.session.commit()
            return True

        return False

    except Exception as e:
        db.session.rollback()
        raise e
