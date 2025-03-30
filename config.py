# 应用程序配置
APP_CONFIG = {
    'app': {
        'title': "考试刷题系统",
        'version': "2.1.3",
        'organization': "记得晚安",
        'copyright': "© 2024 记得晚安. 保留所有权利",
        'author': "记得晚安",
        'contact': "Hatebetray_",
        'font_family': "Microsoft YaHei",
        'font_size': 12,
        'window_width': 1024,
        'window_height': 768
    },
    'exam': {
        'time_limit': 7200,
        'pass_score': 60,
        'questions_file': "1231.txt"
    }
}

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',     # 修改为本地测试数据库
    'port': 3306,
    'user': 'root',         # 修改为测试账号
    'password': '******',   # 修改为测试密码
    'database': 'exam_db',  # 修改为测试数据库名
    'pool_size': 5,
    'auth_plugin': 'mysql_native_password',
    'charset': 'utf8mb4',
    'connect_timeout': 30,
    'connection_attempts': 3,
    'connection_timeout': 10000,
    'pool_reset_session': True
}

# 日志配置
LOG_DIR = 'logs' 