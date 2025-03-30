import os
import shutil
import subprocess
from config import APP_CONFIG
import sys

def clean_dirs():
    """清理旧的构建文件"""
    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            
    for pattern in files_to_clean:
        os.system(f'del /f /q {pattern}')

def install_requirements():
    """安装必要的依赖"""
    requirements = [
        'pyinstaller',
        'PyQt5',
        'mysql-connector-python',
        'wmi',
        'pywin32',
        'DBUtils',
        'psutil'
    ]
    
    for req in requirements:
        subprocess.run(['pip', 'install', req], check=True)

def build_exe():
    """打包程序"""
    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--clean',
        '--debug=all',
        '--icon', 'app.ico',
        '--add-data', 'utils;utils',
        '--add-data', 'config.py;.',
        '--add-data', 'config.json;.',
        '--collect-all', 'PyQt5',
        '--collect-all', 'mysql.connector',
        '--collect-all', 'DBUtils',
        '--hidden-import', 'PyQt5.sip',
        '--hidden-import', 'PyQt5.QtCore',
        '--hidden-import', 'PyQt5.QtGui',
        '--hidden-import', 'PyQt5.QtWidgets',
        '--hidden-import', 'mysql.connector',
        '--hidden-import', 'mysql.connector.plugins',
        '--hidden-import', 'DBUtils.PooledDB',
        '--hidden-import', 'utils',
        '--paths', '.',
        '--runtime-hook', 'hooks.py',
        '--name', APP_CONFIG['app']['title'],
        'run.py'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        
        # 复制必要的运行时文件
        runtime_files = [
            'LICENSE.txt'
        ]
        
        # 创建dist目录（如果不存在）
        if not os.path.exists('dist'):
            os.makedirs('dist')
            
        # 只复制存在的文件
        for file in runtime_files:
            if os.path.exists(file):
                shutil.copy2(file, 'dist')
                print(f"已复制: {file}")
            else:
                print(f"警告: 找不到文件 {file}")
                
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {str(e)}")
        raise
    except Exception as e:
        print(f"复制文件失败: {str(e)}")
        raise

def main():
    try:
        print("开始打包...")
        print("1. 清理旧文件...")
        clean_dirs()
        
        print("2. 安装依赖...")
        install_requirements()
        
        print("3. 打包程序...")
        build_exe()
        
        print("打包完成!")
        
    except Exception as e:
        print(f"打包失败: {str(e)}")
    
    input("按任意键继续...")

if __name__ == '__main__':
    main() 