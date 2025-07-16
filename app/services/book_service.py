import json
import logging
import os
import re
import uuid

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub
from flask import request, jsonify
from sqlalchemy import or_, func
from werkzeug.utils import secure_filename

from app.config import Config
from app.extensions import db, redis_client
from app.models.book import Book
from app.models.bookContent import BookContent
from app.models.payment_history import PaymentHistory
from app.models.user import User
from app.services.sensitive import load_sensitive_words  # 导入敏感词处理模块
from app.utils.payparms import serverUrl

logging.basicConfig(level=logging.DEBUG)

UPLOAD_FOLDER = 'uploads/books'
# 读取敏感词列表
SENSITIVE_WORDS = load_sensitive_words(os.path.join(os.getcwd(), 'sensitiveWord/sensitive_words_lines.txt'))


def generate_unique_directory():
    """生成唯一的 UUID 作为目录名"""
    return str(uuid.uuid4())


def recommend_Books(user_id):
    # 使用 SQLAlchemy 的随机排序功能
    recommended_books = Book.query.order_by(func.random()).limit(3).all()

    # 构造返回的书籍信息
    result = []
    for book in recommended_books:
        result.append({
            "id": book.book_id,
            "name": book.title,
            "desc": book.description[:100] + "..." if book.description else "No description",
            "author": book.author,
            "category": book.category,
            "price": str(book.price) if book.is_paid else "Free",
            "total_pages": book.total_number,
            "free_pages": book.free_pages,
            "label": book.is_paid,
            "url": f"{serverUrl}/static/{book.cover_image}"
        })

    return jsonify({"recommended_books": result}), 200


def search_books():
    # 获取查询参数
    keyword = request.args.get('keyword', '').strip()  # 获取搜索关键字
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400

    # 查询数据库
    try:
        # 使用 SQLAlchemy 的 or_ 实现多字段搜索
        books = Book.query.filter(
            or_(
                Book.title.ilike(f'%{keyword}%'),  # 书名模糊匹配
                Book.author.ilike(f'%{keyword}%')  # 作者模糊匹配
            )
        ).all()

        # 将查询结果转换为字典列表
        result = [{
            "id": book.book_id,
            "name": book.title,
            "desc": book.description[:100] + "..." if book.description else "No description",  # 简化描述（截取前100个字符）
            "author": book.author,
            "category": book.category if book.category else "No category",  # 书籍分类
            "price": str(book.price) if book.is_paid else "Free",  # 如果是收费书籍，显示价格
            "total_pages": book.total_number,  # 总页数
            "free_pages": book.free_pages,  # 免费页数
            "label": book.is_paid,  # 是否收费
            "url": serverUrl + "/static/" + book.cover_image,  # 封面图片URL，假设返回的是相对路径或URL
        } for book in books]

        return jsonify({"books": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def upload_book():
    if not request.content_type or not request.content_type.startswith('multipart/form-data'):
        return jsonify({"error": "Invalid Content-Type. Expected 'multipart/form-data'."}), 415

    logging.debug("Request content type: %s", request.content_type)
    logging.debug("Form data: %s", request.form)
    logging.debug("Files: %s", request.files)

    # 获取书籍信息
    title = request.form.get('title')
    author = request.form.get('author')
    description = request.form.get('description')
    category = request.form.get('category')  # 分类字段
    is_paid = request.form.get('is_paid', 'false').lower() == 'true'
    free_pages = request.form.get('free_pages', 'false').lower() == 'true'
    price = request.form.get('price', '0.0')
    file = request.files.get('file')  # 书籍文件

    # 检查必要字段
    try:
        price = float(price)
    except ValueError:
        return jsonify({"error": "Invalid price format. Must be a numeric value."}), 400

    if not title or not author or not description or not file:
        return jsonify({"error": "Title, author, description, and book file are required."}), 400

    # 创建唯一目录存储书籍文件
    unique_dir = generate_unique_directory()
    book_folder = os.path.join(UPLOAD_FOLDER, unique_dir)

    try:
        os.makedirs(book_folder, exist_ok=True)

        # 保存书籍文件
        filename = secure_filename(file.filename)
        if (filename == 'epub'):
            filename = 'book.epub'
        file_path = os.path.join(book_folder, filename)
        file.save(file_path)
        catalog = {}
        # 检查是否为epub文件
        if filename.lower().endswith('.epub'):
            # 从epub文件中提取封面图片和总页数
            book = epub.read_epub(file_path)

            cover = next(book.get_items_of_type(ebooklib.ITEM_COVER))
            if cover:
                cover_path = os.path.join(book_folder, re.split(r'[/\\]', cover.file_name)[-1])
                cover_path = cover_path.replace('\\', '/')
                with open(cover_path, 'wb') as f:
                    f.write(cover.content)
            else:
                return jsonify({"error": "no cover"}), 400
            for item in book.get_items():
                if item.get_type() != ebooklib.ITEM_DOCUMENT and item.get_type() != ebooklib.ITEM_COVER and item.get_type() != ebooklib.ITEM_NAVIGATION:
                    with open(os.path.join(book_folder, re.split(r'[/\\]', item.file_name)[-1]), 'wb') as f:
                        f.write(item.content)
            for item in book.toc:
                catalog[str(item.title).replace('.', '_')] = book.get_item_with_href(item.href).content.decode('utf-8')
            total_number = len(list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)))  # 初始化总页数
        else:
            return jsonify({"error": "Invalid file format. Only .epub files are supported."}), 400
        book_folder = book_folder.replace('\\', '/')
        # 创建并保存新的书籍对象
        new_book = Book(
            title=title,
            author=author,
            description=description,
            category=category,  # 书籍分类
            total_number=total_number,  # 书籍总页数
            cover_image=cover_path,
            free_pages=free_pages,
            is_paid=is_paid,
            price=price,
            store_path=book_folder,  # 存储路径
        )

        db.session.add(new_book)
        db.session.commit()
        new_book_content = BookContent(book_id=new_book.book_id, chapterContents=catalog)
        new_book_content.save()
        logging.debug("Book saved to database: ID %d", new_book.book_id)
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"message": "Book uploaded successfully", "book_id": new_book.book_id}), 201

    except Exception as e:
        db.session.rollback()
        logging.exception("Error during book upload")
        return jsonify({"error": f"An error occurred during upload: {str(e)}"}), 500


import shutil


def delete_book_by_id(book_id):
    # 查询书籍记录
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found."}), 404

    try:
        # 删除存储文件夹及其内容
        if book.store_path and os.path.exists(book.store_path):
            shutil.rmtree(book.store_path)

        # 删除数据库记录
        db.session.delete(book)
        db.session.commit()

        return jsonify({"message": "Book deleted successfully."}), 200

    except Exception as e:
        logging.exception("Error during book deletion")
        return jsonify({"error": f"An error occurred while deleting the book: {str(e)}"}), 500


def parse_ncx(epub_book):
    """解析NCX文件，返回一个字典，键为playOrder，值为对应的src"""
    ncx_items = [item for item in epub_book.get_items() if item.get_type() == ebooklib.ITEM_NAVIGATION]
    if not ncx_items:
        return {}

    ncx_content = ncx_items[0].content.decode('utf-8')
    soup = BeautifulSoup(ncx_content, 'xml')
    nav_points = soup.find_all('navPoint')

    toc_dict = {}
    for nav_point in nav_points:
        play_order = int(nav_point.get('playOrder'))
        content_src = nav_point.find('content').get('src')
        toc_dict[play_order] = content_src

    return toc_dict


def replace_paths(html_content, book_id, base_path):
    """
    替换 HTML 内容中的路径为本地路径，并将 CSS、JS 和图片文件内容注入到 HTML 中
    :param html_content: 原始 HTML 内容
    :param book_id: 书籍 ID
    :param base_path: 基础路径
    :return: 修改后的 HTML 内容
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # 定义一个函数来生成新的绝对路径
    def generate_absolute_path(relative_path, book_id, base_path):
        # 去掉 relative_path 中的 ../ 部分
        filename = relative_path.split('/')[-1]
        # 拼接成新的绝对路径
        return f"{base_path}{book_id}/{filename}"

    # 定义一个函数来判断路径是否为本地路径
    def is_local_path(path):
        return not (path.startswith('http://') or path.startswith('https://'))

    # 替换 link 标签的 href，并注入 CSS 内容
    for link in soup.find_all('link', href=True):
        original_href = link['href']
        if is_local_path(original_href):  # 只处理本地路径
            link['href'] = generate_absolute_path(original_href, book_id, base_path)

    # 替换 script 标签的 src，并注入 JS 内容
    for script in soup.find_all('script', src=True):
        original_src = script['src']
        if is_local_path(original_src):  # 只处理本地路径
            script['src'] = generate_absolute_path(original_src, book_id, base_path)

    # 替换 img 标签的 src，并注入 Base64 图片数据
    for img in soup.find_all('img', src=True):
        original_src = img['src']
        if is_local_path(original_src):  # 只处理本地路径
            img['src'] = generate_absolute_path(original_src, book_id, base_path)
    for source in soup.find_all('source', src=True):
        original_src = source['src']
        if is_local_path(original_src):  # 只处理本地路径
            source['src'] = generate_absolute_path(original_src, book_id, base_path)
    return str(soup)


def read_page(book_id, filepath):
    try:
        cache_key = f"book:{book_id}:page:{filepath}"
        if Config.REDIS_ENABLED:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                print(f"命中{cache_key}")
                return jsonify({"page_content": json.loads(cached_data)}), 200
        # 使用聚合查询，只提取 chapterContents 中的指定键，支持键名中包含 .
        result = BookContent.objects(book_id=book_id).aggregate([
            {"$project": {
                "chapter_value": f"$chapterContents.{filepath}",
                "_id": 0
            }}
        ])

        # 提取结果
        result_list = list(result)
        if not result_list or result_list[0].get("chapter_value") is None:
            return jsonify({"error": f"Chapter '{filepath}' not found."}), 404
        html_content = result_list[0].get("chapter_value")
        # 替换路径并注入 CSS、JS 和图片内容
        base_path = serverUrl + "/static/epub/"
        modified_html_content = replace_paths(html_content, book_id, base_path)
        if Config.REDIS_ENABLED:
            redis_client.set(cache_key, json.dumps(modified_html_content), ex=Config.EXPIRY_SECONDS)
        return jsonify({"page_content": modified_html_content}), 200
    except Exception as e:
        logging.exception("Error during page read")
        return jsonify({"error": f"An error occurred while reading the book: {str(e)}"}), 500


def get_contents(book_id):
    try:
        cache_key = f"book:{book_id}:contents"
        if Config.REDIS_ENABLED:
            cached_contents = redis_client.get(cache_key)
            if cached_contents:
                print(f'命中{cache_key}')
                return jsonify({"contents": json.loads(cached_contents)}), 200
        book_content = BookContent.objects.get(book_id=book_id)
        if not book_content:
            return jsonify({"error": "Book content not found."}), 404
        contents = [{'title': key, 'href': key} for key in book_content.chapterContents.keys()]
        if Config.REDIS_ENABLED:
            redis_client.set(cache_key, json.dumps(contents), ex=Config.EXPIRY_SECONDS)
        return jsonify({"contents": contents}), 200

    except Exception as e:
        logging.exception("Error during getting contents")
        return jsonify({"error": f"An error occurred while fetching the book contents: {str(e)}"}), 500


def get_books():
    try:
        # 获取请求参数，默认值为0
        cursor = int(request.args.get('cursor', 0))
        count = int(request.args.get('count', 10))
        cache_key = f"book:{cursor}:{count}"
        if Config.REDIS_ENABLED:
            # 尝试从 Redis 获取缓存的书籍目录
            cached_contents = redis_client.get(cache_key)
            if cached_contents:
                print(f'命中{cache_key}')
                return jsonify(json.loads(cached_contents)), 200

        # 根据cursor和count分页查询
        books_query = Book.query.offset(cursor).limit(count).all()

        # 构建返回的书籍数据列表
        books = []
        for book in books_query:
            book_data = {
                "id": book.book_id,
                "name": book.title,
                "desc": book.description[:100] + "..." if book.description else "No description",  # 简化描述（截取前100个字符）
                "author": book.author,
                "category": book.category if book.category else "No category",  # 书籍分类
                "price": str(book.price),  # 如果是收费书籍，显示价格
                "total_pages": book.total_number,  # 总页数
                "free_pages": book.free_pages,  # 免费页数
                "label": book.is_paid,  # 是否收费
                "url": f"{serverUrl}/static/{book.cover_image}" if book.cover_image else f"{serverUrl}/static/uploads/logo.png",
                # 封面图片URL，假设返回的是相对路径或URL
                "created_at": book.created_at.isoformat(),  # 创建时间
            }
            books.append(book_data)
        next_cursor = cursor + count if len(books_query) == count else None
        if Config.REDIS_ENABLED:
            redis_client.set(cache_key, json.dumps({
                "cursor": next_cursor,  # 返回下一页的游标，如果没有更多数据则返回None
                "count": count,
                "books": books
            }), ex=Config.EXPIRY_SECONDS)
        # 获取下一页游标（用于分页）

        print(count, len(books_query), next_cursor)
        # 返回结果
        return jsonify({
            "cursor": next_cursor,  # 返回下一页的游标，如果没有更多数据则返回None
            "count": count,
            "books": books
        }), 200

    except Exception as e:
        # 记录异常并返回错误消息
        logging.exception("Error while fetching books list")
        return jsonify({"error": f"An error occurred while fetching books: {str(e)}"}), 500


def has_user_purchased_book(user_id, book_id):
    """
    查询用户是否已经购买过指定书籍
    如果书籍是免费的，默认返回已购买
    """
    # 获取书籍
    book = Book.query.get(book_id)

    if not book:
        return False  # 如果书籍不存在，返回 False

    # 如果书籍是免费的，直接返回 True，表示已购买
    if not book.is_paid:
        return True

    # 否则，检查用户是否已经购买过该书
    payment = PaymentHistory.query.filter_by(user_id=user_id, book_id=book_id).first()
    return payment is not None  # 如果找到支付记录，则返回 True，表示已购买


def purchase_book(user_id, book_id):
    """
    购买书籍的逻辑：检查余额、扣款、记录支付历史
    """
    # 获取用户和书籍
    user = User.query.get(user_id)
    book = Book.query.get(book_id)

    # 检查用户和书籍是否存在
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not book:
        return jsonify({"error": "Book not found"}), 404

    # 检查是否已经购买过该书
    if has_user_purchased_book(user_id, book_id):
        return jsonify({"error": "You have already purchased this book"}), 400

    # 如果是付费书籍，检查余额是否足够
    if book.is_paid:
        if user.balance < book.price:
            return jsonify({"error": "Insufficient balance"}), 400

        # 扣除用户余额
        user.balance -= book.price

    # 创建支付记录
    payment = PaymentHistory(
        user_id=user.user_id,
        book_id=book.book_id,
        amount=book.price if book.is_paid else 0  # 只有付费书籍才记录金额
    )

    # 提交数据库事务
    try:
        db.session.add(payment)
        db.session.commit()

        # 更新用户余额（如果是付费书籍）
        if book.is_paid:
            db.session.commit()

        return jsonify({
            "message": "Payment successful",
            "new_balance": str(user.balance)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Payment failed", "details": str(e)}), 500
