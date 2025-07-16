from flask import request, jsonify, Blueprint
from app.services.book_service import upload_book, delete_book_by_id, read_page, get_contents, get_books, purchase_book, \
    has_user_purchased_book, search_books, recommend_Books
from app.services.shelf_service import add_book_to_shelf, remove_book_from_shelf, get_user_shelf
UPLOAD_FOLDER = 'uploads/books'

book_bp = Blueprint('book', __name__)

@book_bp.route('/upload', methods=['POST'])
def upload():
    return upload_book()
@book_bp.route('search', methods=['GET'])
def searchBooks():
    return search_books()
@book_bp.route('/recommend',methods=['POST'])
def recommendBooks():
    # user_id = request.json.get('user_id')
    return recommend_Books(None)
@book_bp.route('/delete/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    return delete_book_by_id(book_id)

@book_bp.route('/read/<int:book_id>/page/<path:filename>', methods=['GET'])
def read_book_page(book_id, filename):
    return read_page(book_id, filename)

@book_bp.route('/contents/<int:book_id>', methods=['GET'])
def get_book_contents(book_id):
    return get_contents(book_id)

@book_bp.route('/books', methods=['GET'])
def books():
    return get_books()

# 购买书籍接口
@book_bp.route('/purchase', methods=['POST'])
def purchase():
    user_id = request.json.get('user_id')
    book_id = request.json.get('book_id')

    if not user_id or not book_id:
        return jsonify({"error": "User ID and Book ID are required"}), 400

    # 调用购买书籍的逻辑
    return purchase_book(user_id, book_id)

@book_bp.route('/has_purchased', methods=['POST'])
def has_purchased():
    user_id = request.json.get('user_id')
    book_id = request.json.get('book_id')

    if not user_id or not book_id:
        return jsonify({"error": f"User ID{user_id} and Book ID{book_id} are required"}), 400

    # 调用查询方法
    purchased = has_user_purchased_book(user_id, book_id)

    return jsonify({"purchased": purchased}), 200



@book_bp.route('/shelf/add', methods=['POST'])
def add_to_shelf():
    user_id = request.json.get('user_id')
    book_id = request.json.get('book_id')

    if not user_id or not book_id:
        return jsonify({"error": "User ID and Book ID are required"}), 400

    return add_book_to_shelf(user_id, book_id)

@book_bp.route('/shelf/remove', methods=['POST'])
def remove_from_shelf():
    user_id = request.json.get('user_id')
    book_id = request.json.get('book_id')

    if not user_id or not book_id:
        return jsonify({"error": "User ID and Book ID are required"}), 400

    return remove_book_from_shelf(user_id, book_id)

@book_bp.route('/shelf', methods=['POST'])
def get_shelf():
    user_id = request.get_json().get('user_id')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    return get_user_shelf(user_id)
