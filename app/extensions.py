import logging

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from redis import Redis
from mongoengine import  connect
from app.config import Config

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
redis_client = Redis.from_url(Config.REDIS_URL)
mongo_client =connect(host=Config.MONGO_URL)
# 设置 pymongo 的日志级别为 WARNING 或更高
logging.getLogger("pymongo").setLevel(logging.WARNING)