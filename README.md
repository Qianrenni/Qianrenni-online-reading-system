
- [一、项目结构](#一项目结构)
- [二、快速上手](#二快速上手)

# 一、项目结构

```shell
├── app/
|   ├── admin_ad_routes.py # 管理员广告路由
|   ├── config.py # 配置文件
|   ├── extensions.py # 扩展文件(数据库,redis等引用)
|   ├── keys/ # 密钥文件
|   |   ├── alipay_public_key.pem
|   |   └── app_private_key.pem
|   ├── models/
|   |   ├── advertisement.py # 广告
|   |   ├── book.py # 书籍
|   |   ├── bookContent.py # 书籍内容
|   |   ├── PasswordResetToken.py #重置密码操作记录表
|   |   ├── payment_history.py #支付历史
|   |   ├── readingHistroy.py #阅读历史
|   |   ├── recharge_history.py #充值历史
|   |   ├── shelf.py #书架
|   |   ├── user.py #用户
|   |   ├── userAdvertisement.py #用户观看广告记录表
|   ├── routes/
|   |   ├── admin_route.py #管理员路由
|   |   ├── advertisement_route.py #广告路由
|   |   ├── auth_routes.py #用户认证路由
|   |   ├── book_routes.py #书籍路由
|   |   ├── payment_routes.py #支付路由
|   |   ├── reading_records_routes.py #阅读记录路由
|   |   ├── recharge_routes.py #充值路由
|   |   ├── static_routes.py #静态资源路由
|   |   ├── ui_route.py #服务器端UI路由
|   |   ├── __init__.py
|   ├── services/
|   |   ├── auth_service.py #用户认证服务
|   |   ├── book_service.py #书籍服务 
|   |   ├── reading_records_service.py #阅读记录服务
|   |   ├── recharge_service.py #充值服务
|   |   ├── sensitive.py #敏感词过滤函数
|   |   ├── shelf_service.py #书架服务
|   ├── templates/ #模板页面
|   |   ├── index.html #服务端主页
|   |   └── reset_password.html #重置密码页面
|   ├── utils/ #工具类
|   |   ├── adminidentity.py #管理员身份验证
|   |   ├── batchhandelepub.py #批量处理书籍并上传到数据库
|   |   ├── payparms.py #支付参数,以及服务器路由
|   ├── __init__.py
├── docker-compose.yml #编排部署docker-compose文件
├── Dockerfile #dockerfile文件用于构建镜像
├── README.md #项目说明文件
├── requirements.txt #项目依赖包
├── run.py #项目启动文件
├── sensitiveWord/ #敏感词文件
|   └── sensitive_words_lines.txt
```

# 二、快速上手

- **实际使用的依赖包**

  ```shell
  pip install pipreqs
  pipreqs . --encoding=utf8 --force
  ```

- **安装依赖包**

  ```
  pip3 install -r requirements.txt
  ```

- **启动项目**

  ```
  python3 run.py
  ```
