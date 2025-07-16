from flask import Blueprint, request, jsonify, send_file, Response, render_template
ui_bp = Blueprint('ui', __name__)
@ui_bp.route('/reward', methods=['GET'])
def indexPage():
    # 返回首页内容
    return render_template('index.html', message="多谢支持,我们将继续提高质量!")
