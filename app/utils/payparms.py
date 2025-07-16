import os
serverUrl=os.getenv("SERVER_URL", "http://127.0.0.1:80")
appid = 9021000143674377
return_url = serverUrl+'/reward'
notify_url = serverUrl+"/recharge/api/notify"
app_private_key_string = None
alipay_public_key_string = None


def load_key():
    global app_private_key_string, alipay_public_key_string

    # 定义文件路径
    private_key_path = os.path.join(os.getcwd(), "app/keys/app_private_key.pem")
    public_key_path =os.path.join(os.getcwd(), "app/keys/alipay_public_key.pem")

    try:
        # 检查文件是否存在
        if not os.path.exists(private_key_path):
            raise FileNotFoundError(f"私钥文件不存在: {private_key_path}")
        if not os.path.exists(public_key_path):
            raise FileNotFoundError(f"公钥文件不存在: {public_key_path}")

        # 读取私钥
        with open(private_key_path, 'r') as file:
            app_private_key_string = file.read()

        # 读取公钥
        with open(public_key_path, 'r') as file:
            alipay_public_key_string = file.read()

        print("密钥加载成功！")
    except FileNotFoundError as e:
        print(f"文件未找到: {e}")
    except PermissionError as e:
        print(f"权限错误: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

load_key()