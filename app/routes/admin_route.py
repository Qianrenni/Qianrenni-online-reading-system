import json
import os
import re
from datetime import datetime
from urllib.parse import unquote

from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from app.config import Config
from app.extensions import db, redis_client
from app.models.advertisement import Advertisement
from app.models.book import Book
from app.models.bookContent import BookContent
from app.models.payment_history import PaymentHistory
from app.models.readingHistroy import ReadingHistory
from app.models.recharge_history import RechargeHistory
from app.models.user import User
from app.services.book_service import replace_paths
from app.utils.adminidentity import admin_required
from app.utils.payparms import serverUrl

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users', methods=['GET'])
@jwt_required()  # 验证 Token
@admin_required
def get_users():
    try:
        # 获取当前用户的身份信息（可选）
        # 查询所有用户信息
        users = User.query.all()

        # 构造用户列表
        user_list = [
            {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                # 'role': user.role,
                'balance': str(user.balance),  # Numeric 类型需要转换为字符串
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_active': user.is_active,
                'updated_at': user.updated_at.strftime('%Y-%m-%d %H:%M') if user.updated_at else None,
            }
            for user in users if user.role == 'user'
        ]

        # 返回 JSON 响应
        return jsonify({
            'users': user_list
        }), 200

    except Exception as e:
        # 处理异常
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/disableuser', methods=['POST'])
@jwt_required()  # 验证 Token
@admin_required
def disable_user():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        user = User.query.get(user_id)
        if user:
            user.is_active = False
            db.session.commit()
            return jsonify({'message': 'User disabled successfully'}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/enableuser', methods=['POST'])
@jwt_required()  # 验证 Token
@admin_required
def enable_user():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        user = User.query.get(user_id)
        if user:
            user.is_active = True
            db.session.commit()
            return jsonify({'message': 'User enabled successfully'}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/books/updatebooks', methods=['POST'])
@jwt_required()  # 验证 Token
@admin_required
def update_books():
    try:
        data = request.get_json()
        book = Book.query.get(data.get('bookId'))
        if book:
            book.title = data.get('name')
            book.author = data.get('author')
            book.description = data.get('description')
            book.category = data.get('category')
            book.price = data.get('price') if data.get('is_paid') else 0
            book.is_paid = data.get('is_paid')
            book.free_pages = data.get('free_pages') if data.get('is_paid') else 0
            db.session.commit()
            return jsonify({'message': 'Book updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()  # 验证 Token
@admin_required
def dashboard():
    # 获取当前时间
    now = datetime.utcnow()
    # 倒推 12 个月计算月活用户数
    from dateutil.relativedelta import relativedelta
    mau_data = []
    months = []
    for i in range(12):
        # 定义时间窗口（从早到晚）
        start_date = now - relativedelta(months=i + 1)  # 精确到月份
        end_date = now - relativedelta(months=i)

        # 统计该时间窗口内的活跃用户数
        active_users = (
            db.session.query(ReadingHistory.user_id)
            .filter(ReadingHistory.start_time.between(start_date, end_date))
            .distinct()
            .count()
        )

        # 保存结果
        mau_data.append(active_users)
        months.append(end_date.strftime('%m'))  # 使用结束日期作为月份标识
    # 构造返回数据
    monthly_active_users_data = {
        'categories': months[::-1],  # 时间顺序从早到晚
        'series': [{'name': '月活用户数', 'data': mau_data[::-1], 'color': '#4682B4'}]
    }
    # 按月份统计新建用户数量
    monthly_new_users = (
        db.session.query(
            db.func.date_format(User.created_at, '%Y-%m').label('month'),  # 使用 DATE_FORMAT
            db.func.count(User.user_id).label('count')
        )
        .group_by('month')
        .order_by('month')
        .all()
    )
    # 构造每月用户数数据
    total_users_per_month = []
    # 总用户数
    total_users = 0
    for item in monthly_new_users:
        total_users += item.count
        total_users_per_month.append(total_users)

    monthly_user_data = {
        'categories': [item.month for item in monthly_new_users],
        'series': [
            {'name': '用户数', 'data': [item for item in total_users_per_month], 'color': '#1890FF'}
        ],
    }

    # 总收入（支付历史 + 充值历史）
    total_revenue_payment = float(db.session.query(db.func.sum(PaymentHistory.amount)).scalar() or 0)
    total_revenue_recharge = float(db.session.query(db.func.sum(RechargeHistory.amount)).scalar() or 0)
    total_revenue = total_revenue_payment + total_revenue_recharge

    # 书籍阅读量趋势（按月份统计）
    book_reading_trend = (
        db.session.query(
            db.func.date_format(ReadingHistory.start_time,'%Y-%m-%d').label('month'),  # 提取年月
            db.func.count(ReadingHistory.reading_id).label('count')  # 统计阅读记录数
        )
        .group_by('month')  # 按年月分组
        .order_by('month')  # 按年月排序
        .all()
    )
    book_reading_trend_data = {
        'categories': [item.month for item in book_reading_trend],
        'series': [{'name': '阅读量', 'data': [item.count for item in book_reading_trend], 'color': '#87CEEB'}]
    }

    # 热门书籍阅读量
    hot_books_reading = (
        db.session.query(Book.title, db.func.count(ReadingHistory.reading_id).label('count'))
        .join(ReadingHistory, Book.book_id == ReadingHistory.book_id)
        .group_by(Book.title)
        .order_by(db.desc('count'))
        .limit(5)
        .all()
    )
    hot_books_reading_data = {
        'categories': [item.title for item in hot_books_reading],
        'series': [{'name': '阅读量', 'data': [item.count for item in hot_books_reading], 'color': '#FF69B4'}]
    }

    # 用户活跃度分布（按周统计）
    user_activity_distribution = (
        db.session.query(
            db.func.date_format(ReadingHistory.start_time,'%w').label('day_of_week'),
            db.func.count(ReadingHistory.reading_id).label('count')
        )
        .group_by('day_of_week')
        .order_by('day_of_week')
        .all()
    )
    days_of_week = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
    user_activity_distribution_data = {
        'categories': [days_of_week[int(item.day_of_week)] for item in user_activity_distribution],
        'series': [{'name': '活跃度', 'data': [item.count for item in user_activity_distribution], 'color': '#FFA07A'}]
    }

    # 用户留存率（假设以注册用户为基准）
    retention_rate = []
    for i in range(12):  # 计算最近 12 个月的留存率
        # 定义时间窗口
        start_date = now - relativedelta(months=i + 1)
        end_date = now - relativedelta(months=i)

        # 获取新用户（注册并有阅读记录的用户）
        new_users_query = (
            db.session.query(User.user_id)
            .join(ReadingHistory, User.user_id == ReadingHistory.user_id)
            .filter(User.created_at.between(start_date, end_date))
            .distinct()
        )
        new_users = new_users_query.count()

        # 获取留存用户（在下一个时间窗口内有阅读记录的新用户）
        next_start_date = end_date
        next_end_date = now - relativedelta(months=i)
        retained_users = (
            db.session.query(ReadingHistory.user_id)
            .filter(ReadingHistory.start_time.between(next_start_date, next_end_date))
            .filter(ReadingHistory.user_id.in_(new_users_query.subquery()))
            .distinct()
            .count()
        )

        # 计算留存率
        retention_rate.append((retained_users / new_users * 100) if new_users else 0)

    user_retention_data = {
        'categories': months[::-1],  # 时间顺序从早到晚
        'series': [{'name': '留存率', 'data': retention_rate[::-1], 'color': '#FFD700'}]
    }

    # 收入来源占比
    revenue_sources = {
        '购买': total_revenue_payment,
        '充值': total_revenue_recharge,
    }
    revenue_sources_data = {
        'categories': list(revenue_sources.keys()),
        'series': [
            {'name': key, 'data': value, 'color': ['#1890FF', '#2FC25B'][i]}
            for i, (key, value) in enumerate(revenue_sources.items())
        ]
    }

    # 收入增长趋势（按月份统计）
    revenue_growth = (
        db.session.query(
            db.func.date_format(PaymentHistory.payment_time,'%Y-%m').label('month'),
            db.func.sum(PaymentHistory.amount).label('total')
        )
        .group_by('month')
        .order_by('month')
        .all()
    )

    # 构造收入增长数据
    categories = []
    growth_data = []

    for i, item in enumerate(revenue_growth):
        categories.append(item.month)  # 年月作为分类
        if i == 0:
            growth_data.append(item.total)  # 第一个月没有前一个月，直接使用总收入
        else:
            growth_value = item.total - revenue_growth[i - 1].total  # 当前月减去前一个月
            growth_data.append(growth_value)

    revenue_growth_data = {
        'categories': categories,
        'series': [
            {
                'name': '收入增长',
                'data': growth_data,
                'color': '#1E90FF',
            }
        ],
    }

    # 返回结果
    return jsonify({
        'totalUsers': {
            'categories': [{'name': '用户数', 'min': 0, 'max': max(total_users, 10000)}],
            'series': [{'name': '当前', 'data': total_users}]
        },
        "totalUsersTrend": monthly_user_data,
        'totalRevenueTrend': {
            'categories': [item.month for item in revenue_growth],
            'series': [{'name': '收入', 'data': [item.total for item in revenue_growth], 'color': '#FACC14'}]
        },
        "monthlyActiveUsers": {
            "categories": [{"name": '月活', "min": 0, "max": 300}],
            "series": [{"name": '当前', "data": mau_data[0]}]
        },
        'monthlyActiveUsersTrend': monthly_active_users_data,
        'totalRevenue': {
            'categories': [{'name': '收入', 'min': 0, 'max': max(total_revenue, 100000)}],
            'series': [{'name': '当前', 'data': total_revenue}]
        },
        'bookReadingTrend': book_reading_trend_data,
        'hotBooksReading': hot_books_reading_data,
        'userActivityDistribution': user_activity_distribution_data,
        'userRetention': user_retention_data,
        'revenueSources': revenue_sources_data,
        'revenueGrowth': revenue_growth_data
    }), 200


@admin_bp.route('/updateBookChapter', methods=['POST'])
@jwt_required()  # 验证 Token
@admin_required
def updateBookChapter():
    try:
        # 获取表单参数
        book_id = request.form.get('bookId')
        href = request.form.get('href')
        if not book_id or not href:
            return jsonify({"error": "Missing required parameters."}), 400

        # 获取 HTML 文件
        html_file = request.files.get('html')
        if not html_file:
            return jsonify({"error": "HTML file not found."}), 400

        # 获取书籍记录
        book = Book.query.get(book_id)
        if not book:
            return jsonify({"error": "Book not found."}), 404

        # 获取书籍文件所在的目录
        book_directory = os.path.join(os.getcwd(), book.store_path)
        if not os.path.exists(book_directory):
            return jsonify({"error": "Book directory not found."}), 404
        # 查询 book_id 对应的文档
        book_content = BookContent.objects.get(book_id=book_id)
        if not book_content:
            return jsonify({"error": "Chapter not found in the EPUB file."}), 404

        # 读取并解析 HTML 文件
        html_content = html_file.read().decode('utf-8')
        soup = BeautifulSoup(html_content, 'html.parser')

        # 添加图片和视频资源到 EPUB 文件
        for key, value in request.files.items():
            if key=='html':
                continue
            filename=unquote( re.split(r'[/\\]', value.filename)[-1])
            if os.path.exists(os.path.join(book_directory, filename)):
                continue
            value.save(os.path.join(book_directory,filename))


        # 更新 HTML 内容中的资源路径
        for img in soup.find_all('img'):
            if 'src' in img.attrs and 'alt' in img.attrs:
                img['src'] = img['alt']
                if 'data-href' in img.attrs:
                    del img['data-href']

        for video in soup.find_all('video'):
            source = video.find('source')
            if source and 'src' in source.attrs and 'poster' in video.attrs:
                source['src'] = video['poster']

        # 更新 MongoDB 中的章节内容
        book_content.update(**{f"set__chapterContents__{href}": str(soup)})
        cache_key = f"book:{book_id}:page:{href}"
        print(str(soup))
        if Config.REDIS_ENABLED:
            base_path = serverUrl + "/static/epub/"
            modified_html_content = replace_paths(str(soup), book_id, base_path)
            redis_client.set(cache_key, json.dumps(modified_html_content), ex=Config.EXPIRY_SECONDS)
        return jsonify({
            "message": "Chapter updated successfully",
        }), 200

    except FileNotFoundError as e:
        return jsonify({"error": f"File not found: {str(e)}"}), 404
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred.{str(e)} "}), 500


@admin_bp.route('/advertisement', methods=['GET'])
@jwt_required()  # 验证 Token
@admin_required
def get_advertisement():
    advertisements = Advertisement.query.all()
    return jsonify({
        "advertisements": [
            {
                "ad_id": ad.ad_id,
                "name": ad.name,
                "description": ad.description,
                "video_url": f"{serverUrl}/static/{ad.video_url}",
                "reward": float(ad.reward),  # 确保数值类型兼容 JSON
                "is_active": ad.is_active,
                "duration": ad.duration
            }
            for ad in advertisements
        ]
    }), 200


@admin_bp.route('/advertisement/add', methods=['POST'])
def add_ad():
    """
    添加广告视频。
    :return: 成功或失败的消息
    """
    try:
        # 获取表单数据
        name = request.form.get('name')
        description = request.form.get('description', '')
        duration = request.form.get('duration')
        reward = request.form.get('reward')
        is_active = request.form.get('is_active')

        # 验证必填字段
        if not name or not duration or not reward:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400

        # 确保时长和奖励金额为有效数字
        try:
            duration = int(duration)
            reward = float(reward)
        except ValueError:
            return jsonify({'success': False, 'message': '时长或奖励金额格式错误'}), 400

        # 确保是否启用字段为布尔值
        is_active = True if is_active == 'true' else False

        # 处理视频文件上传
        video_file = request.files.get('video_file')
        if not video_file:
            return jsonify({'success': False, 'message': '未上传视频文件'}), 400

        # 确保文件名安全
        filename = secure_filename(video_file.filename)

        # 创建存储目录（如果不存在）
        upload_folder = os.path.join(os.getcwd(), 'uploads', 'video')
        os.makedirs(upload_folder, exist_ok=True)

        # 保存视频文件
        file_path = os.path.join(upload_folder, filename)
        video_file.save(file_path)

        # 构造视频文件的访问 URL
        video_url = f"uploads/video/{filename}"

        # 创建广告记录
        new_ad = Advertisement(
            name=name,
            description=description,
            duration=duration,
            reward=reward,
            is_active=is_active,
            video_url=video_url
        )
        db.session.add(new_ad)
        db.session.commit()

        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '广告添加成功',
            'ad_id': new_ad.ad_id,
            'video_url': f"{serverUrl}/static/{video_url}"
        }), 200

    except Exception as e:
        # 捕获异常并返回错误信息
        print(f"Error adding advertisement: {str(e)}")
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500


@admin_bp.route('/advertisement/update', methods=['POST'])
def update_ad():
    """
    更新广告信息。
    :return: 成功或失败的消息
    """
    try:
        # 获取表单数据
        ad_id = request.form.get('ad_id')
        name = request.form.get('name')
        description = request.form.get('description', '')
        duration = request.form.get('duration')
        reward = request.form.get('reward')
        is_active = request.form.get('is_active')

        # 验证必填字段
        if not ad_id or not name or not duration or not reward:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400

        # 确保时长和奖励金额为有效数字
        try:
            duration = int(duration)
            reward = float(reward)
        except ValueError:
            return jsonify({'success': False, 'message': '时长或奖励金额格式错误'}), 400

        # 确保是否启用字段为布尔值
        is_active = True if is_active == 'true' else False

        # 查询广告记录
        ad = Advertisement.query.filter_by(ad_id=ad_id).first()
        if not ad:
            return jsonify({'success': False, 'message': '广告不存在'}), 404

        # 处理视频文件上传
        video_file = request.files.get('video')  # 注意：这里的字段名必须与前端一致（如 'video'）
        if video_file:
            # 删除旧的视频文件（如果存在）
            if ad.video_url:
                old_video_path = os.path.join(os.getcwd(), ad.video_url)
                if os.path.exists(old_video_path):
                    os.remove(old_video_path)

            # 确保文件名安全
            filename = secure_filename(video_file.filename)
            if not filename:
                return jsonify({'success': False, 'message': '无效的文件名'}), 400

            # 创建存储目录（如果不存在）
            upload_folder = os.path.join(os.getcwd(), 'uploads', 'video')
            os.makedirs(upload_folder, exist_ok=True)

            # 保存新视频文件
            file_path = os.path.join(upload_folder, filename)
            video_file.save(file_path)

            # 构造视频文件的访问 URL
            video_url = f"uploads/video/{filename}"
            ad.video_url = video_url  # 更新广告的视频 URL

        # 更新其他广告信息
        ad.name = name
        ad.description = description
        ad.duration = duration
        ad.reward = reward
        ad.is_active = is_active

        # 提交更改到数据库
        db.session.commit()

        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '广告更新成功',
            'ad_id': ad.ad_id,
            'video_url': f"{serverUrl}/static/{ad.video_url}" if ad.video_url else None
        }), 200

    except Exception as e:
        # 捕获异常并返回错误信息
        print(f"Error updating advertisement: {str(e)}")
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500


@admin_bp.route('/advertisements/delete', methods=['POST'])
def delete_advertisement():
    """
    删除广告。
    :return: 成功或失败的消息
    """
    try:
        # 获取 ad_id
        ad_id = request.get_json().get('ad_id')

        # 验证 ad_id 是否存在
        if not ad_id:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400

        # 查询广告记录
        ad = Advertisement.query.filter_by(ad_id=ad_id).first()
        if not ad:
            return jsonify({'success': False, 'message': '广告不存在'}), 404

        # 删除关联的视频文件（如果存在）
        if ad.video_url:
            video_path = os.path.join(os.getcwd(), ad.video_url)
            if os.path.exists(video_path):
                os.remove(video_path)

        # 删除广告记录
        db.session.delete(ad)
        db.session.commit()

        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '广告删除成功',
            'ad_id': ad_id
        }), 200

    except Exception as e:
        # 捕获异常并返回错误信息
        print(f"Error deleting advertisement: {str(e)}")
        db.session.rollback()  # 回滚事务以避免数据库损坏
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500
