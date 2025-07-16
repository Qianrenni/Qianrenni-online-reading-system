from app.models.readingHistroy import ReadingHistory
from app.models.shelf import Shelf
from app.models.book import Book
from app.models.user import User
from app.extensions import db
from flask import jsonify

from app.utils.payparms import serverUrl


def add_book_to_shelf(user_id, book_id):
    # 检查用户和书籍是否存在
    user = User.query.get(user_id)
    book = Book.query.get(book_id)

    if not user:
        return jsonify({"error": "User not found"}), 404
    if not book:
        return jsonify({"error": "Book not found"}), 404

    # 检查书籍是否已在用户书架上
    existing_shelf = Shelf.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_shelf:
        return jsonify({"error": "Book already exists in the shelf"}), 400

    # 创建书架记录
    shelf = Shelf(
        user_id=user_id,
        book_id=book_id
    )

    try:
        db.session.add(shelf)
        db.session.commit()
        return jsonify({"message": "Book added to shelf successfully", "shelf_id": shelf.shelf_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred while adding book to shelf: {str(e)}"}), 500

def remove_book_from_shelf(user_id, book_id):
    # 查找用户的书架记录
    shelf_record = Shelf.query.filter_by(user_id=user_id, book_id=book_id).first()

    if not shelf_record:
        return jsonify({"error": "Book not found in the shelf"}), 404

    try:
        db.session.delete(shelf_record)
        db.session.commit()
        return jsonify({"message": "Book removed from shelf successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred while removing book from shelf: {str(e)}"}), 500

def get_user_shelf(user_id):
    # 获取用户书架上的所有书籍
    shelf_records = Shelf.query.filter_by(user_id=user_id).all()

    if not shelf_records:
        return jsonify({"shelf":[]}), 200

    # 获取书籍详细信息
    books = []
    for record in shelf_records:
        book = Book.query.get(record.book_id)
        reading_history =ReadingHistory.query.filter_by(user_id=user_id, book_id=record.book_id).order_by(ReadingHistory.created_at.desc()).first()
        if book:
            books.append({
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
                'read':reading_history.last_read_page if reading_history else 1,
            })

    return jsonify({"shelf": books}), 200
