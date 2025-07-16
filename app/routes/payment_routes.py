
from flask import Blueprint, send_from_directory, jsonify, request
from app.extensions import db
from app.models.book import Book
from app.models.payment_history import PaymentHistory

payment_bp = Blueprint('payment', __name__)
@payment_bp.route('/get', methods=['POST'])
def get():
    userId = request.json.get('userId')
    if not userId:
        return jsonify({"error": "User ID is required."}), 400
    result= db.session.query(PaymentHistory, Book)\
        .join(Book, PaymentHistory.book_id == Book.book_id)\
        .filter(PaymentHistory.user_id == userId).all()
    data=[]
    for item in result:
        payment_history, book = item
        data.append({
            "book_id": book.book_id,
            "title": book.title,
            "author": book.author,
            "price": book.price,
            "create_date": payment_history.payment_time.strftime("%Y-%m-%d %H:%M"),
            "payment_id": payment_history.payment_id
        })
    return jsonify(data),200



