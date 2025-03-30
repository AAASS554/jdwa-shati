from .crypto import SecurityProvider

class DatabaseCrypto:
    def __init__(self):
        self.security = SecurityProvider()

    def encrypt(self, data):
        if isinstance(data, str):
            return self.security.encrypt(data)
        return data

    def decrypt(self, data):
        if isinstance(data, str):
            return self.security.decrypt(data)
        return data 