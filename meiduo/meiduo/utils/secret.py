from django.conf import settings
# 使用 TimedJSONWebSignatureSerializer 对象 可以设置有效期
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
class SecretOauth(object):
    def __init__(self):
        # 1.根据 签名(secret_key) 创建序列化对象
        self.serializer = Serializer(secret_key=settings.SECRET_KEY, expires_in=24 * 15 * 60)

    # 加密
    def dumps(self, content_dict):
        # 1. 通过 dumps方法 加密数据
        result = self.serializer.dumps(content_dict)
        # 2. result是bytes类型转换成 str
        return result.decode()

    # 解密
    def loads(self, content_dict):
        try:
            # 1. 通过 loads方法 解密数据
            result = self.serializer.loads(content_dict)
        except Exception as e:
            print(e)
            # 解密失败返回None
            return None

        # 2. 返回解密完毕数据
        return result

