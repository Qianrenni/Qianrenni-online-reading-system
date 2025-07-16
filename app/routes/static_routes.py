import io

from flask import Blueprint, request, jsonify, send_file, Response, render_template

from app.config import Config
from app.extensions import redis_client
from app.models.book import Book
from flask import Blueprint, send_from_directory, jsonify, request
import os
# 定义蓝图
static_bp = Blueprint('static', __name__)

# 图片存储路径（相对于项目根目录）
UPLOADS_FOLDER = os.path.join(os.getcwd(), 'uploads')

@static_bp.route('/uploads/<path:filepath>', methods=['GET'])
def get_image(filepath):
    """
    提供对 uploads 文件夹下图片的公共访问路径
    :param filepath: 图片的相对路径
    """
    try:
        cache_key = f'image:{filepath}'
        filename= filepath.split('/')[-1]
        if Config.REDIS_ENABLED:
            # 尝试从 Redis 缓存中获取文件内容
            cache_content = redis_client.get(cache_key)
            if cache_content:
                print(f'命中 {cache_key}')
                # 将字节流包装为文件对象
                file_object = io.BytesIO(cache_content)
                return send_file(file_object, as_attachment=False,download_name=filename)

        # 拼接完整路径
        full_path = os.path.join(UPLOADS_FOLDER, filepath)

        # 检查文件是否存在
        if not os.path.exists(full_path):
            return jsonify({"error": "File not found"}), 404

        # 读取文件内容
        with open(full_path, 'rb') as file:
            file_content = file.read()
            # 将文件内容写入 Redis 缓存（如果启用）
            if Config.REDIS_ENABLED:
                redis_client.set(cache_key, file_content, ex=Config.EXPIRY_SECONDS)
            # 返回文件
            return send_file(io.BytesIO(file_content),as_attachment=False,download_name=filename)
    except Exception as e:
        print(f'An error occurred while accessing the resource: {str(e)}')
        return jsonify({"error": str(e)}), 500


@static_bp.route('/epub/<string:book_id>/<path:resource_path>', methods=['GET'])
def get_epub_resource(book_id, resource_path):
    """
    提供对 EPUB 格式中静态资源（如图片、CSS 等）的访问
    :param book_id: 书籍的 ID
    :param resource_path: 资源的相对路径
    """
    try:
        cache_key = f'epub:{book_id}:{resource_path}'
        filename= resource_path.split('/')[-1]
        if Config.REDIS_ENABLED:
            # 尝试从 Redis 缓存中获取文件内容
            cache_content = redis_client.get(cache_key)
            if cache_content:
                print(f'命中 {cache_key}')
                # 将字节流包装为文件对象
                file_object = io.BytesIO(cache_content)
                return send_file(file_object, as_attachment=False, download_name=filename)
        # 查询书籍记录
        book = Book.query.get(book_id)
        if not book:
            return jsonify({"error": "Book not found."}), 404

        # 获取书籍文件所在的目录
        targetFile = os.path.join(os.getcwd(),book.store_path,resource_path)
        if not os.path.exists(targetFile):
            return jsonify({"error": "targetFile not found."}), 404
        with open(targetFile, 'rb') as file:
            file_content = file.read()
            if Config.REDIS_ENABLED:
                redis_client.set(cache_key, file_content, ex=Config.EXPIRY_SECONDS)
            return send_file(io.BytesIO(file_content), as_attachment=False,download_name=filename)
    except Exception as e:
        return jsonify({"error": f"An error occurred while accessing the resource: {str(e)}"}), 500

