import  pickle
import base64

class CookieSecret(object):
    @classmethod
    def dumps(cls,data):
        data_bates = pickle.dumps(data)
        base64_bytes = base64.b64encode(data_bates)

        base64_bytes = base64_bytes.decode()
        return base64_bytes
    @classmethod
    def loads(cls,data):
        #data = data.encode()
        base64_bytes = base64.b64decode(data)
        data_bates = pickle.loads(base64_bytes)
        return data_bates