import hashlib
import base64

class SecurityProvider:
    def __init__(self, key=b'YourSecretKey123'):
        self.key = hashlib.sha256(key).digest()

    def encrypt(self, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            return base64.b64encode(data).decode()
        except:
            return data

    def decrypt(self, data):
        try:
            if isinstance(data, str):
                return base64.b64decode(data).decode()
            return data
        except:
            return data 