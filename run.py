import sys
import os
import traceback
import logging
from datetime import datetime

# 配置日志
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f'error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    logging.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

def init_qt():
    """初始化Qt环境"""
    try:
        # 设置环境变量
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
        os.environ['QT_SCALE_FACTOR'] = '1'
        os.environ['QT_SCREEN_SCALE_FACTORS'] = '1'
        
        # PyQt5相关导入
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5 import QtCore
        
        # 设置高DPI支持
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        return app
        
    except Exception as e:
        logging.critical(f"Qt初始化失败: {str(e)}\n{traceback.format_exc()}")
        raise

def init_app(app):
    """初始化应用程序"""
    try:
        from config import APP_CONFIG
        
        # 设置应用程序属性
        app.setApplicationName(APP_CONFIG['app']['title'])
        app.setApplicationVersion(APP_CONFIG['app']['version'])
        app.setOrganizationName(APP_CONFIG['app']['organization'])
        
        # 设置全局字体
        from PyQt5.QtGui import QFont
        font = QFont(APP_CONFIG['app']['font_family'], APP_CONFIG['app']['font_size'])
        app.setFont(font)
        
    except Exception as e:
        logging.critical(f"应用程序初始化失败: {str(e)}\n{traceback.format_exc()}")
        raise

def main():
    try:
        # 初始化Qt
        app = init_qt()
        
        # 初始化应用程序
        init_app(app)
        
        # 导入主程序
        from exam import ExamSystem
        
        try:
            # 创建主窗口
            window = ExamSystem()
            window.show()
            
            # 运行应用
            return app.exec_()
            
        except Exception as e:
            logging.critical(f"主窗口创建失败: {str(e)}\n{traceback.format_exc()}")
            print(f"程序启动失败，详细信息请查看日志文件: {log_file}")
            return 1
            
    except Exception as e:
        logging.critical(f"程序启动失败: {str(e)}\n{traceback.format_exc()}")
        print(f"程序启动失败，详细信息请查看日志文件: {log_file}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 