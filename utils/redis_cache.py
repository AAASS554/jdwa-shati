"""Redis缓存模块"""
import redis
import json
import hashlib
from functools import wraps
from config import REDIS_CONFIG

try:
    import redis
except ImportError:
    print("警告: redis模块未安装，将使用无缓存模式")
    redis = None

class RedisCache:
    _instance = None
    
    @staticmethod
    def get_instance():
        if RedisCache._instance is None:
            RedisCache._instance = RedisCache()
        return RedisCache._instance
        
    def __init__(self):
        try:
            self.redis = redis.Redis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'],
                password=REDIS_CONFIG['password'],
                decode_responses=REDIS_CONFIG['decode_responses']
            )
        except Exception as e:
            print(f"Redis连接失败: {e}")
            self.redis = None
    
    def _generate_key(self, prefix, *args, **kwargs):
        """生成缓存键"""
        data = f"{str(args)}:{str(kwargs)}"
        return f"{prefix}:{hashlib.md5(data.encode()).hexdigest()}"
    
    def cache_query(self, prefix='query', expire_time=None):
        """查询缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.redis:
                    return func(*args, **kwargs)
                    
                key = self._generate_key(prefix, *args, **kwargs)
                
                # 尝试从缓存获取
                try:
                    cached = self.redis.get(key)
                    if cached:
                        return json.loads(cached)
                except:
                    return func(*args, **kwargs)
                
                # 执行查询
                result = func(*args, **kwargs)
                
                # 存入缓存
                try:
                    self.redis.setex(
                        key,
                        expire_time or REDIS_CONFIG['expire_time'],
                        json.dumps(result)
                    )
                except:
                    pass
                
                return result
            return wrapper
        return decorator
    
    def cache_card_status(self, card_key, status, expire=None):
        """缓存卡密状态"""
        if not self.redis:
            return
            
        try:
            key = f"card:status:{card_key}"
            self.redis.setex(
                key,
                expire or REDIS_CONFIG['expire_time'],
                json.dumps(status)
            )
        except:
            pass
    
    def get_card_status(self, card_key):
        """获取卡密状态"""
        if not self.redis:
            return None
            
        try:
            key = f"card:status:{card_key}"
            status = self.redis.get(key)
            return json.loads(status) if status else None
        except:
            return None
    
    def invalidate_cache(self, pattern='*'):
        """清除指定模式的缓存"""
        if not self.redis:
            return
            
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except:
            pass
    
    def cache_questions(self, questions, subject):
        """缓存题库"""
        if not self.redis:
            return
            
        try:
            key = f"questions:{subject}"
            self.redis.setex(
                key,
                REDIS_CONFIG['expire_time'],
                json.dumps(questions)
            )
        except:
            pass
    
    def get_cached_questions(self, subject):
        """获取缓存的题库"""
        if not self.redis:
            return None
            
        try:
            key = f"questions:{subject}"
            questions = self.redis.get(key)
            return json.loads(questions) if questions else None
        except:
            return None 
    
    def cache_with_fallback(self, key, callback, expire=3600):
        """带有降级处理的缓存方法"""
        try:
            # 尝试从缓存获取
            if self.redis:
                data = self.redis.get(key)
                if data:
                    return json.loads(data)
            
            # 缓存未命中，执行回调
            result = callback()
            
            # 写入缓存
            if self.redis:
                self.redis.setex(key, expire, json.dumps(result))
            
            return result
        except:
            return callback()

    def set(self, key, value, expire=None):
        """设置缓存"""
        if not self.redis:
            return False
        try:
            self.redis.set(key, value)
            if expire:
                self.redis.expire(key, expire)
            return True
        except:
            return False
            
    def get(self, key):
        """获取缓存"""
        if not self.redis:
            return None
        try:
            return self.redis.get(key)
        except:
            return None
            
    def delete(self, key):
        """删除缓存"""
        if not self.redis:
            return False
        try:
            return self.redis.delete(key)
        except:
            return False 