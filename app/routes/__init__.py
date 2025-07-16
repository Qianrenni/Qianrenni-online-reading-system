from app.routes.admin_route import admin_bp
from app.routes.auth_routes import auth_bp
from app.routes.book_routes import book_bp
from app.routes.payment_routes import payment_bp
from app.routes.reading_records_routes import reading_records_bp
from app.routes.recharge_routes import recharge_route
from app.routes.static_routes import static_bp  # 导入静态文件蓝图
from app.routes.ui_route import ui_bp
from app.routes.advertisement_route import advertisement_bp


def register_blueprints(app):
    """
    注册所有蓝图到应用中
    """
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(book_bp, url_prefix='/book')
    app.register_blueprint(reading_records_bp, url_prefix='/readingrecord')
    app.register_blueprint(recharge_route, url_prefix='/recharge')
    app.register_blueprint(static_bp, url_prefix='/static')  # 注册静态文件蓝图
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(ui_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(advertisement_bp, url_prefix='/ad')
