from flask import Flask
from app.routes import register_blueprints
from flask_docs import ApiDoc
from app.extensions import db,jwt,mail
from flask_cors import CORS
def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    # 文件上传大小限制
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 16MB 文件上传限制
    app.config['MAIL_SERVER'] = 'smtp.qq.com'
    app.config['MAIL_PORT'] = '465'
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = '3277958121@qq.com'
    app.config['MAIL_PASSWORD'] = 'abxkatndvxdsdcaf'  # 在 QQ 邮箱设置中生成
    app.config['MAIL_DEFAULT_SENDER'] = '3277958121@qq.com'  # ✅ 设置默认发件人
    CORS(app, resources={r"/*": {"origins": r"*"}})

    # 初始化扩展
    db.init_app(app)  # 确保调用了 init_app
    jwt.init_app(app)
    mail.init_app(app)
    # 注册蓝图
    register_blueprints(app)

    ApiDoc(
        app,
        title="Sample App",
        version="1.0.0",
        description="A simple app API",
    )
    return app
