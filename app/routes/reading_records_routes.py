from flask import request, jsonify, Blueprint
from app.services.reading_records_service import add_reading_history,delete_reading_history, get_reading_history
reading_records_bp = Blueprint('reading_records',__name__)

@reading_records_bp.route('/add', methods=['POST'])
def add():
    return add_reading_history()

@reading_records_bp.route('/delete', methods=['DELETE'])
def delete():
    return delete_reading_history()

@reading_records_bp.route('/get', methods=['POST'])
def get():
    return get_reading_history()   