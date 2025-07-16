
from app import create_app
from app.extensions import db
from app.utils.batchhandelepub import run
# 创建 Flask 应用
app = create_app()
# 确保在上下文中执行数据库操作
try:
    with app.app_context():
        db.create_all()  # 初始化数据库表
except Exception as e:
    print(f"Error initializing database: {e}")
if __name__ == '__main__':
    # 确保 run() 在应用上下文中执行
    with app.app_context():
        run()

    # 启动 Flask 应用
    app.run(debug=True, port=80)
