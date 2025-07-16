import os


def str_to_bool(value, default=False):
    """
    将字符串转换为布尔值。
    :param value: 环境变量的值（字符串）
    :param default: 默认值（如果无法解析时返回）
    :return: 转换后的布尔值
    """
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
    return default


class Config:
    SECRET_KEY = 'your_secret_key'

    # 数据库配置
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    # SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "OnlineReading.db")}'  # 数据库文件名
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "mysql+pymysql://root:123456@127.0.0.1:3306/reading")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # JWT 配置
    JWT_SECRET_KEY = 'your_jwt_secret_key'
    MONGO_URL = os.getenv("MONGO_URL", 'mongodb://localhost:27017/reading')
    # 从环境变量中获取 REDIS_URL，如果不存在则使用默认值
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    # 从环境变量中获取 REDIS_ENABLED，默认值为 False
    REDIS_ENABLED = str_to_bool(os.getenv("REDIS_ENABLED"), default=True)

    # 从环境变量中获取 SENSITIVE_ENABLED，默认值为 False
    SENSITIVE_ENABLED = str_to_bool(os.getenv("SENSITIVE_ENABLED"), default=False)
    EXPIRY_SECONDS = 300