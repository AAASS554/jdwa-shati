from dbutils.pooled_db import PooledDB
import mysql.connector
from config import DB_CONFIG
import logging

class DatabasePool:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            try:
                # 分离连接池配置和数据库配置
                db_config = DB_CONFIG.copy()
                
                # 连接池专用配置
                pool_config = {
                    'creator': mysql.connector,
                    'maxconnections': 20,    # 最大连接数
                    'mincached': 5,          # 初始连接数
                    'maxcached': 10,         # 最大缓存连接数
                    'maxshared': 5,          # 最大共享连接数
                    'blocking': True,        # 连接数达到最大时阻塞等待
                    'maxusage': None,        # 连接最大使用次数
                    'ping': 1,               # 检查连接是否有效
                    'reset': True,           # 重置连接
                    'autocommit': True       # 自动提交
                }
                
                self._pool = PooledDB(
                    **pool_config,
                    **db_config
                )
            except Exception as e:
                logging.error(f"初始化连接池失败: {str(e)}")
                raise
    
    def get_connection(self):
        try:
            return self._pool.connection()
        except Exception as e:
            logging.error(f"获取数据库连接失败: {str(e)}")
            raise 