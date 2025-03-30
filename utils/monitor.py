import logging
import time
from datetime import datetime
from functools import wraps
from utils.redis_cache import RedisCache
from utils.db_pool import DatabasePool
import os
from logging.handlers import RotatingFileHandler

class SystemMonitor:
    def __init__(self):
        self.redis_cache = RedisCache.get_instance()
        logging.basicConfig(
            filename='logs/system.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 添加文件处理器
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # 设置日志轮转
        handler = RotatingFileHandler(
            'logs/system.log',
            maxBytes=1024*1024,  # 1MB
            backupCount=5
        )
        logging.getLogger().addHandler(handler)
    
    @staticmethod
    def performance_monitor(threshold=1.0):
        """性能监控装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if duration > threshold:
                    logging.warning(
                        f"性能警告: {func.__name__} 执行时间 {duration:.2f}秒"
                    )
                    
                # 记录到Redis用于统计
                try:
                    RedisCache.get_instance()._redis.hincrby(
                        f"perf:stats:{func.__name__}",
                        "total_calls",
                        1
                    )
                    RedisCache.get_instance()._redis.hincrbyfloat(
                        f"perf:stats:{func.__name__}",
                        "total_time",
                        duration
                    )
                except:
                    pass
                    
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def log_error(e, operation):
        """记录错误日志"""
        logging.error(f"{operation} 失败: {str(e)}")
    
    def check_system_health(self):
        """检查系统健康状态"""
        health_status = {
            'database': self._check_database(),
            'redis': self._check_redis(),
            'performance': self._check_performance()
        }
        return health_status
    
    def _check_database(self):
        """检查数据库连接"""
        try:
            with DatabasePool().get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logging.error(f"数据库检查失败: {str(e)}")
            return False
    
    def _check_redis(self):
        """检查Redis连接"""
        try:
            self.redis_cache._redis.ping()
            return True
        except:
            logging.error("Redis检查失败")
            return False
    
    def _check_performance(self):
        """检查系统性能"""
        try:
            stats = {}
            for key in self.redis_cache._redis.keys("perf:stats:*"):
                func_stats = self.redis_cache._redis.hgetall(key)
                if func_stats:
                    total_calls = int(func_stats.get(b'total_calls', 0))
                    total_time = float(func_stats.get(b'total_time', 0))
                    avg_time = total_time / total_calls if total_calls > 0 else 0
                    stats[key.decode().split(':')[-1]] = {
                        'total_calls': total_calls,
                        'avg_time': avg_time
                    }
            return stats
        except Exception as e:
            logging.error(f"性能检查失败: {str(e)}")
            return {} 

    @performance_monitor(threshold=1.0)
    def monitor_system_health(self):
        """监控系统健康状态"""
        stats = {
            'memory': self.get_memory_usage(),
            'cpu': self.get_cpu_usage(),
            'disk': self.get_disk_usage(),
            'network': self.get_network_status()
        }
        
        # 记录监控数据
        self.log_stats(stats)
        
        # 检查阈值
        self.check_thresholds(stats) 