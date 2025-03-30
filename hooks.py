import os
import sys
import logging
import traceback
from datetime import datetime

def init_logging():
    """初始化日志"""
    try:
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, f'error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 添加控制台输出
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        logging.getLogger('').addHandler(console)
        
        logging.info("日志系统初始化成功")
    except Exception as e:
        with open('error.log', 'w') as f:
            f.write(f"日志初始化失败: {str(e)}\n{traceback.format_exc()}")

def init_environment():
    """初始化运行环境"""
    try:
        # 添加当前目录到Python路径
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        os.chdir(application_path)
        if application_path not in sys.path:
            sys.path.insert(0, application_path)
            
        # 添加DLL搜索路径
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(application_path)
            
        # 设置Python DLL路径
        if hasattr(sys, '_MEIPASS'):
            # 添加pywin32 DLL路径
            pywin32_system32 = os.path.join(sys._MEIPASS, 'pywin32_system32')
            if os.path.exists(pywin32_system32):
                os.environ['PATH'] = f"{pywin32_system32};{os.environ['PATH']}"
            
            # 添加其他DLL路径
            os.environ['PATH'] = f"{sys._MEIPASS};{os.environ['PATH']}"
            
        # 设置环境变量
        os.environ['PYTHONPATH'] = application_path
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        
        logging.info(f"环境初始化成功: {application_path}")
        
    except Exception as e:
        logging.error(f"环境初始化失败: {str(e)}\n{traceback.format_exc()}")

def run():
    """运行时钩子"""
    try:
        init_logging()
        init_environment()
        logging.info("运行时钩子执行完成")
    except Exception as e:
        with open('hook_error.log', 'w') as f:
            f.write(f"运行时钩子失败: {str(e)}\n{traceback.format_exc()}") 