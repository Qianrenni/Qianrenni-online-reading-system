# app/routes/admin/ad_routes.py

from flask import Blueprint, request, jsonify
from app.models.advertisement import Advertisement
from app.extensions import db
from werkzeug.utils import secure_filename
import os

# 创建蓝图对象
ad_manage_bp = Blueprint('ad_manage', __name__, url_prefix='/admin/ad')

# 假设视频文件存储在 uploads 目录下
UPLOAD_FOLDER = 'app/static/uploads/ads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}  # 允许的文件类型
MAX_FILE_SIZE = 50 * 1024 * 1024  # 最大文件大小：50MB


# 检查文件类型是否允许
def allowed_file(filename):
    """
    检查上传的文件是否是允许的类型。
    :param filename: 文件名
    :return: 如果文件类型允许，返回 True；否则返回 False
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 获取视频时

@ad_manage_bp.route('/', methods=['GET'])
def get_ads():
    """
    获取所有广告信息。
    :return: JSON 格式的广告列表
    """
    ads = Advertisement.query.all()
    return jsonify([{
        'id': ad.id,
        'name': ad.name,
        'description': ad.description,
        'video_url': ad.video_url,
        'is_active': ad.is_active,
        'created_at': ad.created_at,
        'reward_value': ad.reward_value,  # 奖励值
        'duration': ad.duration  # 广告时长
    } for ad in ads])


@ad_manage_bp.route('/add', methods=['POST'])
def add_ad():
    """
    添加广告视频。
    :return: 成功或失败的消息
    """
    if 'file' not in request.files:
        return jsonify({'status': 'failed', 'message': 'No file part'})

    file = request.files['file']
    name = request.form.get('name')
    description = request.form.get('description')
    reward_value = request.form.get('reward_value', type=int)
    duration = request.form.get('duration', type=int)
    # 检查必填字段
    if not name or not description or not reward_value:
        return jsonify({'status': 'failed', 'message': 'Missing required fields'})

    if file and allowed_file(file.filename):
        # 检查文件大小是否超出限制
        if len(file.read()) > MAX_FILE_SIZE:
            return jsonify({'status': 'failed', 'message': 'File size exceeds the limit (50MB)'})

        # 重置文件指针，避免影响后续保存操作
        file.seek(0)

        # 保存文件到指定目录
        filename = secure_filename(file.filename)
        video_url = os.path.join(UPLOAD_FOLDER, filename)
        file.save(video_url)
        if duration is None:
            return jsonify({'status': 'failed', 'message': 'Failed to extract video duration'})

        # 创建广告对象并保存到数据库
        new_ad = Advertisement(
            name=name,
            description=description,
            video_url=video_url,
            reward_value=reward_value,  # 奖励值
            duration=duration  # 自动获取的广告时长
        )
        db.session.add(new_ad)
        db.session.commit()

        return jsonify({'status': 'success', 'message': '广告视频已添加'})
    else:
        return jsonify({'status': 'failed', 'message': 'Invalid file format'})


@ad_manage_bp.route('/edit/<int:ad_id>', methods=['POST'])
def edit_ad(ad_id):
    """
    编辑广告视频。
    :param ad_id: 广告 ID
    :return: 成功或失败的消息
    """
    ad = Advertisement.query.get(ad_id)
    if not ad:
        return jsonify({'status': 'failed', 'message': '广告未找到'})

    name = request.form.get('name')
    description = request.form.get('description')
    is_active = request.form.get('is_active', type=bool)
    reward_value = request.form.get('reward_value', type=int)
    duration = request.form.get('duration', type=int)
    # 检查是否重新上传了视频文件
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            # 检查文件大小是否超出限制
            if len(file.read()) > MAX_FILE_SIZE:
                return jsonify({'status': 'failed', 'message': 'File size exceeds the limit (50MB)'})

            # 重置文件指针，避免影响后续保存操作
            file.seek(0)

            # 删除旧的视频文件（如果存在）
            if ad.video_url and os.path.exists(ad.video_url):
                try:
                    os.remove(ad.video_url)
                except Exception as e:
                    return jsonify({'status': 'failed', 'message': f'Failed to delete old video file: {e}'})

            # 保存新的视频文件
            filename = secure_filename(file.filename)
            video_url = os.path.join(UPLOAD_FOLDER, filename)
            file.save(video_url)
            if duration is None:
                return jsonify({'status': 'failed', 'message': 'Failed to extract video duration'})

            ad.video_url = video_url
            ad.duration = duration  # 更新广告时长

    # 更新其他字段
    if name:
        ad.name = name
    if description:
        ad.description = description
    if is_active is not None:
        ad.is_active = is_active
    if reward_value is not None:
        ad.reward_value = reward_value

    db.session.commit()
    return jsonify({'status': 'success', 'message': '广告已更新'})


@ad_manage_bp.route('/disable/<int:ad_id>', methods=['POST'])
def disable_ad(ad_id):
    """
    禁用广告。
    :param ad_id: 广告 ID
    :return: 成功或失败的消息
    """
    ad = Advertisement.query.get(ad_id)
    if not ad:
        return jsonify({'status': 'failed', 'message': '广告未找到'})

    # 将广告状态设置为禁用
    ad.is_active = False
    db.session.commit()

    return jsonify({'status': 'success', 'message': '广告已禁用'})


@ad_manage_bp.route('/delete/<int:ad_id>', methods=['POST'])
def delete_ad(ad_id):
    """
    删除广告。
    :param ad_id: 广告 ID
    :return: 成功或失败的消息
    """
    ad = Advertisement.query.get(ad_id)
    if not ad:
        return jsonify({'status': 'failed', 'message': '广告未找到'})

    # 删除上传的视频文件（如果存在）
    if ad.video_url and os.path.exists(ad.video_url):
        try:
            os.remove(ad.video_url)
        except Exception as e:
            return jsonify({'status': 'failed', 'message': f'Failed to delete video file: {e}'})

    # 从数据库中删除广告记录
    db.session.delete(ad)
    db.session.commit()

    return jsonify({'status': 'success', 'message': '广告已删除'})
