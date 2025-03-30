import sys
import random
import json
import os
import mysql.connector
import datetime
import wmi
import uuid
import hashlib
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from dbutils.pooled_db import PooledDB
from utils.protection import AntiDebug
from config import APP_CONFIG

class DatabasePool:
    _instance = None
    _pool = None
    
    DB_CONFIG = {
        'host': 'localhost',     # 修改为本地测试数据库
        'user': 'root',         # 修改为测试账号
        'password': '******',   # 修改为测试密码
        'database': 'exam_db',  # 修改为测试数据库名
        'port': 3306,
        'charset': 'utf8mb4',
        'connect_timeout': 60
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if self._pool is None:
            try:
                for attempt in range(self.DB_CONFIG.get('connection_attempts', 3)):
                    try:
                        self._pool = PooledDB(
                            creator=mysql.connector,
                            maxconnections=20,
                            mincached=2,
                            maxcached=5,
                            blocking=True,
                            maxusage=None,
                            ping=1,
                            host=self.DB_CONFIG['host'],
                            user=self.DB_CONFIG['user'],
                            password=self.DB_CONFIG['password'],
                            database=self.DB_CONFIG['database'],
                            port=self.DB_CONFIG['port'],
                            charset=self.DB_CONFIG['charset'],
                            auth_plugin='mysql_native_password',
                            use_pure=True,
                            connect_timeout=self.DB_CONFIG.get('connect_timeout', 30),
                            connection_timeout=self.DB_CONFIG.get('connection_timeout', 10000),
                            pool_reset_session=self.DB_CONFIG.get('pool_reset_session', True)
                        )
                        print(f"数据库连接成功 (尝试 {attempt + 1})")
                        break
                    except Exception as e:
                        if attempt == self.DB_CONFIG.get('connection_attempts', 3) - 1:
                            raise
                        print(f"连接失败 (尝试 {attempt + 1}): {str(e)}")
                        import time
                        time.sleep(2)  # 等待2秒后重试
            except Exception as e:
                print(f"初始化连接池失败: {str(e)}")
                raise
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            return self._pool.connection()
        except Exception as e:
            print(f"获取数据库连接失败: {str(e)}")
            raise

class ExamSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 启动保护
        AntiDebug.start_protection()
        
        # 使用数据库连接池
        self.db_pool = DatabasePool()
        self.db_connection = self.db_pool.get_connection()
        
        # 验证相关属性
        self.is_activated = False
        self.expiry_time = None
        self.current_card_key = None
        self.device_id = self.get_machine_code()
        
        # 考试相关属性
        self.questions = []
        self.wrong_questions = []
        self.current_question = None
        self.score = 0
        self.answered = 0
        self.total_questions = 10
        self.question_history = []
        self.current_index = -1
        self.current_subject = "题库"
        
        # 初始化UI
        self.init_ui()
        
        # 状态更新计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_display)
        self.timer.start(1000)
        
        # 卡密状态检查计时器
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_card_status)
        self.check_timer.start(10000)
        
        # 加载保存的卡密
        saved_card = self.load_config()
        if saved_card:
            self.card_input.setText(saved_card)
            self.remember_checkbox.setChecked(True)  # 如果有保存的卡密，自动勾选复选框
            QTimer.singleShot(500, lambda: self.verify_card(saved_card, self.device_id))
        
        # 添加菜单栏
        self.create_menu()

    def init_ui(self):
        self.setWindowTitle("考试刷题系统 - By 记得晚安")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #EBF5FB;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #AED6F1;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:disabled {
                background-color: #BDC3C7;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #AED6F1;
                border-radius: 4px;
                background: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3498DB;
            }
            QLabel {
                color: #2C3E50;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        
        # 卡密验证部分
        auth_group = QGroupBox("卡密验证")
        auth_layout = QHBoxLayout(auth_group)
        
        self.card_input = QLineEdit()
        self.card_input.setPlaceholderText('请输入卡密...')
        self.card_input.setFixedWidth(200)
        
        auth_btn = QPushButton('验证卡密')
        auth_btn.clicked.connect(self.verify_card_clicked)
        
        # 添加记住卡密复选框
        self.remember_checkbox = QCheckBox('记住卡密')
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                color: #666;
                font-size: 12px;
            }
            QCheckBox:hover {
                color: #333;
            }
        """)
        
        auth_layout.addWidget(QLabel('卡密:'))
        auth_layout.addWidget(self.card_input)
        auth_layout.addWidget(auth_btn)
        auth_layout.addWidget(self.remember_checkbox)  # 添加到布局
        auth_layout.addStretch()
        
        layout.addWidget(auth_group)
        
        # 使用状态显示
        time_group = QGroupBox("使用状态")
        time_layout = QHBoxLayout(time_group)
        
        self.time_label = QLabel('未激活')
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                padding: 8px;
                border: 1px solid #AED6F1;
                border-radius: 4px;
                background: white;
                min-width: 200px;
            }
        """)
        time_layout.addStretch()
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        
        layout.addWidget(time_group)
        
        # 功能区域
        function_group = QGroupBox("功能区")
        function_layout = QVBoxLayout(function_group)
        
        # 功能按钮
        self.import_btn = QPushButton('导入题库')
        self.start_btn = QPushButton('开始答题')
        self.wrong_btn = QPushButton('查看错题本')
        
        function_layout.addWidget(self.import_btn)
        function_layout.addWidget(self.start_btn)
        function_layout.addWidget(self.wrong_btn)
        
        self.import_btn.clicked.connect(self.import_questions)
        self.start_btn.clicked.connect(self.start_exam)
        self.wrong_btn.clicked.connect(self.show_wrong_questions)
        
        # 禁用功能按钮直到验证
        self.import_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.wrong_btn.setEnabled(False)
        
        layout.addWidget(function_group)
        
        # 答题区域
        self.exam_widget = QWidget()
        self.exam_layout = QVBoxLayout(self.exam_widget)
        
        # 题目标签
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 10px;
                background: white;
                border-radius: 4px;
            }
        """)
        self.exam_layout.addWidget(self.question_label)
        
        # 选项按钮
        self.option_group = QButtonGroup()
        self.option_buttons = []
        option_layout = QHBoxLayout()
        
        for i, letter in enumerate(['A', 'B', 'C', 'D']):
            btn = QPushButton(letter)
            btn.setCheckable(True)
            btn.setFixedSize(50, 50)
            self.option_buttons.append(btn)
            self.option_group.addButton(btn, i)
            option_layout.addWidget(btn)
            btn.clicked.connect(self.auto_check_answer)
        
        self.exam_layout.addLayout(option_layout)
        
        # 选项文本
        self.option_labels = []
        for i in range(4):
            label = QLabel()
            label.setWordWrap(True)
            label.setStyleSheet("padding: 5px;")
            self.option_labels.append(label)
            self.exam_layout.addWidget(label)
        
        # 结果标签
        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.hide()
        self.exam_layout.addWidget(self.result_label)
        
        # 导航按钮
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton('上一题')
        self.next_btn = QPushButton('下一题')
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        
        self.prev_btn.clicked.connect(self.show_previous)
        self.next_btn.clicked.connect(self.show_next)
        
        self.exam_layout.addLayout(nav_layout)
        
        # 暂停按钮
        self.pause_btn = QPushButton('暂停答题')
        self.pause_btn.clicked.connect(self.pause_exam)
        self.exam_layout.addWidget(self.pause_btn)
        
        self.exam_widget.hide()
        layout.addWidget(self.exam_widget)
        
        # 作者信息
        author_label = QLabel("作者：记得晚安")
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                padding: 5px;
            }
        """)
        layout.addWidget(author_label)

    def get_machine_code(self):
        """获取机器码"""
        try:
            c = wmi.WMI()
            cpu = c.Win32_Processor()[0].ProcessorId.strip()
            board = c.Win32_BaseBoard()[0].SerialNumber.strip()
            bios = c.Win32_BIOS()[0].SerialNumber.strip()
            machine_code = f"{cpu}-{board}-{bios}"
            return hashlib.md5(machine_code.encode()).hexdigest()
        except:
            return hashlib.md5(str(uuid.getnode()).encode()).hexdigest()

    def verify_card(self, card_key, device_id):
        """验证卡密"""
        try:
            cursor = self.db_connection.cursor()
            
            # 检查卡密是否存在
            cursor.execute("""
                SELECT status, device_id, expiry_time 
                FROM card_keys 
                WHERE card_key = %s
            """, (card_key,))
            
            result = cursor.fetchone()
            if not result:
                QMessageBox.warning(self, '错误', '卡密不存在')
                return
                
            status, bound_device, expiry_time = result
            
            # 检查是否已使用
            if status == 1:
                # 如果已使用，检查是否是当前设备
                if bound_device != device_id:
                    QMessageBox.warning(self, '错误', '卡密已被其他设备使用')
                    return
            
            # 检查是否过期
            if datetime.datetime.now() > expiry_time:
                QMessageBox.warning(self, '错误', '卡密已过期')
                return
                
            # 如果未使用，进行首次激活
            if status == 0:
                cursor.execute("""
                    UPDATE card_keys 
                    SET device_id = %s,
                        status = 1,
                        use_time = NOW(),
                        bind_time = NOW()
                    WHERE card_key = %s
                """, (device_id, card_key))
                self.db_connection.commit()
            
            self.is_activated = True
            self.expiry_time = expiry_time
            self.current_card_key = card_key
            
            # 根据复选框状态决定是否保存卡密
            if self.remember_checkbox.isChecked():
                self.save_config()
            else:
                # 如果不记住卡密，删除配置文件
                try:
                    os.remove('config.json')
                except:
                    pass
            
            # 启用功能按钮
            self.import_btn.setEnabled(True)
            self.start_btn.setEnabled(bool(self.questions))
            self.wrong_btn.setEnabled(bool(self.questions))
            
            QMessageBox.information(self, '成功', '卡密验证成功!')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'验证失败: {str(e)}')
        finally:
            cursor.close()

    def check_card_status(self):
        """检查卡密状态"""
        if not self.is_activated or not self.current_card_key:
            return
            
        cursor = None
        connection = None
        try:
            # 从连接池获取连接
            connection = self.db_pool.get_connection()
            cursor = connection.cursor()
            
            # 使用一次查询获取所有需要的信息
            cursor.execute("""
                SELECT 
                    k.status,
                    k.device_id,
                    k.expiry_time,
                    k.valid_days,
                    k.use_time,
                    CASE 
                        WHEN k.expiry_time < NOW() THEN 0
                        ELSE DATEDIFF(k.expiry_time, NOW())
                    END as remaining_days,
                    c.change_type,
                    c.change_time
                FROM card_keys k
                LEFT JOIN (
                    SELECT card_key, change_type, change_time
                    FROM card_status_change
                    WHERE change_time > DATE_SUB(NOW(), INTERVAL 10 SECOND)
                    ORDER BY change_time DESC
                    LIMIT 1
                ) c ON k.card_key = c.card_key
                WHERE k.card_key = %s
            """, (self.current_card_key,))
            
            result = cursor.fetchone()
            
            if not result:
                print(f"卡密已被删除: {self.current_card_key}")
                self.deactivate("卡密已被删除，请重新购买")
                return
                
            (status, bound_device, expiry_time, valid_days, 
             use_time, remaining_days, change_type, change_time) = result
            
            # 检查状态变更
            if change_type:
                if change_type == 'reset':
                    self.deactivate("卡密已被重置，请重新验证")
                elif change_type == 'unbind':
                    self.deactivate("卡密已被解绑，请重新验证")
                elif change_type == 'disable':
                    self.deactivate("卡密已被禁用")
                return
                
            # 检查卡密状态
            if status == 0:
                self.deactivate("卡密状态异常，请重新验证")
                return
                
            # 检查设备绑定
            if bound_device != self.device_id:
                self.deactivate("卡密已被其他设备使用")
                return
                
            # 检查是否过期
            if datetime.datetime.now() > expiry_time:
                self.deactivate("卡密已过期，请重新购买")
                return
                
            # 更新剩余时间显示
            if remaining_days > 0:
                self.expiry_time = expiry_time
                self.time_label.setText(f'剩余有效期: {remaining_days}天')
                self.time_label.setStyleSheet("""
                    QLabel {
                        color: #67C23A;
                        font-size: 14px;
                        padding: 8px;
                        border: 1px solid #e1f3d8;
                        border-radius: 4px;
                        background: #f0f9eb;
                        min-width: 200px;
                        font-weight: bold;
                    }
                """)
            else:
                self.deactivate("卡密已过期，请重新购买")
                
        except mysql.connector.Error as e:
            print(f"数据库错误: {str(e)}")
            self.deactivate("数据库连接失败，请重试")
        except Exception as e:
            print(f"检查卡密状态失败: {str(e)}")
            self.deactivate("验证状态检查失败")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def deactivate(self, message=None):
        """停用功能"""
        self.is_activated = False
        self.expiry_time = None
        self.current_card_key = None
        
        # 根据复选框状态决定是否清除配置
        if not self.remember_checkbox.isChecked():
            try:
                os.remove('config.json')
            except:
                pass
        
        # 禁用功能按钮
        self.import_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.wrong_btn.setEnabled(False)
        
        # 隐藏答题界面
        self.exam_widget.hide()
        
        # 重置答题状态
        self.answered = 0
        self.score = 0
        self.current_index = -1
        self.question_history = []
        
        if message:
            QMessageBox.warning(self, '警告', message)

    def update_time_display(self):
        """更新时间显示"""
        if not self.is_activated or not self.expiry_time:
            self.time_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 14px;
                    padding: 8px;
                    border: 1px solid #e3e5e7;
                    border-radius: 4px;
                    background: #f6f7f8;
                    min-width: 200px;
                }
            """)
            self.time_label.setText('未激活')
            return
            
        now = datetime.datetime.now()
        if now > self.expiry_time:
            self.deactivate("卡密已过期")
            return
            
        remaining = self.expiry_time - now
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        seconds = remaining.seconds % 60
        
        self.time_label.setStyleSheet("""
            QLabel {
                color: #67C23A;
                font-size: 14px;
                padding: 8px;
                border: 1px solid #e1f3d8;
                border-radius: 4px;
                background: #f0f9eb;
                min-width: 200px;
                font-weight: bold;
            }
        """)
        self.time_label.setText(f'剩余有效期: {days}天 {hours:02d}:{minutes:02d}:{seconds:02d}')

    def import_questions(self):
        """导入题库"""
        if not self.is_activated:
            QMessageBox.warning(self, '提示', '请先验证卡密')
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择题库文件",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self.current_subject = os.path.splitext(os.path.basename(file_path))[0]
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.questions = []
                    
                    # 按题目分割
                    questions_raw = content.split('\n\n')
                    
                    for i, q in enumerate(questions_raw):
                        try:
                            if not q.strip():
                                continue
                                
                            lines = [line.strip() for line in q.split('\n') if line.strip()]
                            
                            # 提取题目
                            title = ''
                            options = []
                            answer = ''
                            
                            # 查找题目
                            for line in lines:
                                if line in ['一、单选题', '二、单选题', '单选题']:
                                    continue
                                if '?' in line or '？' in line or any(line.startswith(f"{n}.") for n in range(1, 1000)):
                                    title = line
                                    break
                            
                            if not title and lines:
                                title = lines[0]
                            
                            # 提取选项
                            for line in lines:
                                if any(line.startswith(prefix) for prefix in ['A.', 'B.', 'C.', 'D.', 
                                                                            'A、', 'B、', 'C、', 'D、',
                                                                            'A ', 'B ', 'C ', 'D ']):
                                    options.append(line)
                                elif '答案' in line or '正确' in line:
                                    for ans in ['A', 'B', 'C', 'D']:
                                        if ans in line:
                                            answer = ans
                                            break
                            
                            # 验证提取的内容
                            if title and len(options) == 4 and answer:
                                question = {
                                    'title': title,
                                    'options': options,
                                    'answer': answer
                                }
                                self.questions.append(question)
                            
                        except Exception as e:
                            print(f"处理题目 {i+1} 时出错: {str(e)}")
                            continue
                    
                    if self.questions:
                        self.setWindowTitle(f'{self.current_subject} - 考试刷题系统')
                        self.start_btn.setEnabled(True)
                        self.wrong_btn.setEnabled(True)
                        QMessageBox.information(self, '成功', 
                                              f'成功导入 {len(self.questions)} 道题目')
                    else:
                        QMessageBox.warning(self, '警告', 
                                          '未能从文件中解析出有效题目，请检查文件格式')
                    
            except Exception as e:
                QMessageBox.critical(self, '错误', f'导入题库失败: {str(e)}')

    def start_exam(self):
        """开始答题"""
        if not self.is_activated:
            QMessageBox.warning(self, '提示', '请先验证卡密')
            return
        
        # 检查是否有题目
        if not self.questions:
            QMessageBox.warning(self, '提示', '请先导入题库')
            return
        
        try:
            if os.path.exists('progress.json'):
                with open('progress.json', 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    
                reply = QMessageBox.question(
                    self, 
                    '继续答题', 
                    f'发现未完成的答题记录:\n'
                    f'已答题数: {progress["answered"]}/{progress["total_questions"]}\n'
                    f'当前得分: {progress["score"]}\n\n'
                    f'是否继续上次的答题？',
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 恢复进度
                    self.answered = progress['answered']
                    self.score = progress['score']
                    self.total_questions = progress['total_questions']
                    os.remove('progress.json')
                else:
                    # 开始新答题
                    os.remove('progress.json')
                    self.answered = 0
                    self.score = 0
                    self.total_questions = len(self.questions)  # 使用实际题目数量
            else:
                # 没有进度文件，直接开始新答题
                self.answered = 0
                self.score = 0
                self.total_questions = len(self.questions)  # 使用实际题目数量
            
            # 隐藏主菜单按钮
            self.import_btn.hide()
            self.start_btn.hide()
            self.wrong_btn.hide()
            
            # 显示答题界面
            self.exam_widget.show()
            
            # 开始显示题目
            self.show_question()
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'开始答题失败: {str(e)}')

    def show_question(self):
        """显示题目"""
        if self.answered < self.total_questions:
            self.current_question = self.questions[self.answered]
            progress = f'进度: {self.answered + 1}/{self.total_questions} ({(self.answered + 1)/self.total_questions*100:.1f}%)\n\n'
            self.question_label.setText(progress + f'题目 {self.answered + 1}:\n{self.current_question["title"]}')
            
            # 重置选项
            for btn in self.option_buttons:
                btn.setChecked(False)
                btn.setEnabled(True)
            
            for i, option in enumerate(self.current_question['options']):
                self.option_labels[i].setText(option)
            
            self.result_label.hide()
            
            # 更新导航按钮状态
            self.prev_btn.setEnabled(len(self.question_history) > 0)
            self.next_btn.setEnabled(False)
        else:
            self.show_result()

    def auto_check_answer(self):
        """自动检查答案"""
        QTimer.singleShot(200, self.check_answer)

    def check_answer(self):
        """检查答案"""
        try:
            checked_button = self.option_group.checkedButton()
            if not checked_button:
                return
            
            answer = chr(ord('A') + self.option_group.id(checked_button))
            
            # 记录答题历史
            history_item = {
                'question': self.current_question,
                'your_answer': answer,
                'is_correct': answer == self.current_question['answer']
            }
            
            self.question_history.append(history_item)
            self.current_index = len(self.question_history) - 1
            
            if answer == self.current_question['answer']:
                self.score += 1
                self.result_label.setText('✓ 回答正确!')
                self.result_label.setStyleSheet("""
                    QLabel {
                        background-color: #4CAF50;
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        margin: 10px;
                    }
                """)
            else:
                self.result_label.setText(f'✗ 回答错误! 正确答案是: {self.current_question["answer"]}')
                self.result_label.setStyleSheet("""
                    QLabel {
                        background-color: #f44336;
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        margin: 10px;
                    }
                """)
                self.wrong_questions.append({
                    'question': self.current_question,
                    'your_answer': answer
                })
            
            self.result_label.show()
            self.answered += 1
            
            # 禁用选项按钮
            for btn in self.option_buttons:
                btn.setEnabled(False)
            
            # 更新导航按钮状态
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(False)
            
            QTimer.singleShot(800, self.next_question)
            
        except Exception as e:
            print(f"检查答案时出错: {str(e)}")
            QMessageBox.critical(self, '错误', f'检查答案时出错: {str(e)}')

    def next_question(self):
        """下一题"""
        self.result_label.hide()
        if self.answered < self.total_questions:
            self.show_question()
        else:
            self.show_result()

    def show_previous(self):
        """显示上一题"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_history_question()
            self.next_btn.setEnabled(True)
            if self.current_index == 0:
                self.prev_btn.setEnabled(False)

    def show_next(self):
        """显示下一题"""
        if self.current_index < len(self.question_history) - 1:
            self.current_index += 1
            self.show_history_question()
            self.prev_btn.setEnabled(True)
            if self.current_index == len(self.question_history) - 1:
                if self.answered < self.total_questions:
                    self.next_btn.setEnabled(True)
                else:
                    self.next_btn.setEnabled(False)
        else:
            if self.answered < self.total_questions:
                self.show_question()

    def show_history_question(self):
        """显示历史题目"""
        history_item = self.question_history[self.current_index]
        self.current_question = history_item['question']
        
        progress = f'进度: {self.current_index + 1}/{self.total_questions} ({(self.current_index + 1)/self.total_questions*100:.1f}%)\n\n'
        self.question_label.setText(progress + f'题目 {self.current_index + 1}:\n{self.current_question["title"]}')
        
        # 重置选项
        for btn in self.option_buttons:
            btn.setChecked(False)
            btn.setEnabled(False)
        
        for i, option in enumerate(self.current_question['options']):
            self.option_labels[i].setText(option)
        
        # 显示历史答案
        answer_index = ord(history_item['your_answer']) - ord('A')
        self.option_buttons[answer_index].setChecked(True)
        
        if history_item['is_correct']:
            self.result_label.setText('✓ 回答正确!')
            self.result_label.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px;
                }
            """)
        else:
            self.result_label.setText(f'✗ 回答错误! 正确答案是: {self.current_question["answer"]}')
            self.result_label.setStyleSheet("""
                QLabel {
                    background-color: #f44336;
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px;
                }
            """)
        self.result_label.show()

    def show_result(self):
        """显示结果"""
        self.save_wrong_questions()
        QMessageBox.information(self, '考试结束', 
                              f'得分: {self.score}/{self.total_questions}\n'
                              f'正确率: {(self.score/self.total_questions)*100:.1f}%')
        
        # 显示主菜单按钮
        self.import_btn.show()
        self.start_btn.show()
        self.wrong_btn.show()
        
        # 隐藏答题界面
        self.exam_widget.hide()

    def show_wrong_questions(self):
        """显示错题本"""
        if not self.is_activated:
            QMessageBox.warning(self, '提示', '请先验证卡密')
            return
            
        if not self.load_wrong_questions():
            QMessageBox.information(self, '提示', '错题本为空!')
            return
            
        wrong_window = QWidget()
        wrong_window.setWindowTitle('错题本')
        wrong_window.setGeometry(350, 350, 800, 600)
        
        layout = QVBoxLayout()
        
        # 添加标题
        title_label = QLabel('错题本')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(title_label)
        
        # 添加统计信息
        stats_label = QLabel(f'共有 {len(self.wrong_questions)} 道错题')
        stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(stats_label)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # 添加错题
        for i, wq in enumerate(self.wrong_questions, 1):
            question_widget = QWidget()
            q_layout = QVBoxLayout()
            
            # 题目
            title = QLabel(f'错题 {i}:')
            title.setFont(QFont('Arial', 12, QFont.Bold))
            q_layout.addWidget(title)
            
            content = QLabel(wq['question']['title'])
            content.setWordWrap(True)
            q_layout.addWidget(content)
            
            # 选项
            for option in wq['question']['options']:
                option_label = QLabel(option)
                option_label.setWordWrap(True)
                q_layout.addWidget(option_label)
            
            # 答案信息
            answer_layout = QHBoxLayout()
            your_answer = QLabel(f'你的答案: {wq["your_answer"]}')
            your_answer.setStyleSheet("color: #e74c3c; font-weight: bold;")
            correct_answer = QLabel(f'正确答案: {wq["question"]["answer"]}')
            correct_answer.setStyleSheet("color: #27ae60; font-weight: bold;")
            
            answer_layout.addWidget(your_answer)
            answer_layout.addWidget(correct_answer)
            q_layout.addLayout(answer_layout)
            
            # 分隔线
            if i < len(self.wrong_questions):
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                q_layout.addWidget(line)
            
            question_widget.setLayout(q_layout)
            scroll_layout.addWidget(question_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton('清空错题本')
        clear_btn.clicked.connect(lambda: self.clear_wrong_questions(wrong_window))
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        export_btn = QPushButton('导出错题本')
        export_btn.clicked.connect(self.export_wrong_questions)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(export_btn)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        layout.addLayout(button_layout)
        
        wrong_window.setLayout(layout)
        wrong_window.show()

    def clear_wrong_questions(self, window):
        """清空错题本"""
        reply = QMessageBox.question(self, '确认', '确定要清空错题本吗？',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.wrong_questions = []
            self.save_wrong_questions()
            window.close()
            QMessageBox.information(self, '提示', '错题本已清空!')

    def export_wrong_questions(self):
        """导出错题本"""
        try:
            filename = f'{self.current_subject}_错题本.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f'====== {self.current_subject}错题本 ======\n\n')
                for i, wq in enumerate(self.wrong_questions, 1):
                    f.write(f'错题 {i}:\n')
                    f.write(f'{wq["question"]["title"]}\n')
                    for option in wq["question"]["options"]:
                        f.write(f'{option}\n')
                    f.write(f'你的答案: {wq["your_answer"]}\n')
                    f.write(f'正确答案: {wq["question"]["answer"]}\n\n')
            QMessageBox.information(self, '提示', f'错题本已导出到 {filename}!')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出错题本失败: {str(e)}')

    def save_wrong_questions(self):
        """保存错题本"""
        filename = f'{self.current_subject}_wrong_questions.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.wrong_questions, f, ensure_ascii=False, indent=2)
            
    def load_wrong_questions(self):
        """加载错题本"""
        try:
            filename = f'{self.current_subject}_wrong_questions.json'
            with open(filename, 'r', encoding='utf-8') as f:
                self.wrong_questions = json.load(f)
                return bool(self.wrong_questions)
        except:
            return False
            
    def pause_exam(self):
        """暂停答题"""
        reply = QMessageBox.question(self, '暂停答题', 
                                   f'当前进度: {self.answered}/{self.total_questions}\n是否保存并退出?',
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            progress = {
                'answered': self.answered,
                'score': self.score,
                'total_questions': self.total_questions
            }
            with open('progress.json', 'w', encoding='utf-8') as f:
                json.dump(progress, f)
            
            # 显示主菜单按钮
            self.import_btn.show()
            self.start_btn.show()
            self.wrong_btn.show()
            
            # 隐藏答题界面
            self.exam_widget.hide()

    def verify_card_clicked(self):
        """验证卡密按钮点击事件"""
        card_key = self.card_input.text().strip()
        if not card_key:
            QMessageBox.warning(self, '提示', '请输入卡密')
            return
        
        # 调用验证方法，传入卡密和设备ID
        self.verify_card(card_key, self.device_id)

    def save_config(self):
        """保存卡密配置"""
        try:
            config = {
                'card_key': self.current_card_key,
                'device_id': self.device_id
            }
            with open('card_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"保存卡密配置失败: {str(e)}")

    def load_config(self):
        """加载卡密配置"""
        try:
            if os.path.exists('card_config.json'):
                with open('card_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if config.get('device_id') == self.device_id:
                        return config.get('card_key')
        except:
            pass
        return None

    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 帮助菜单
        help_menu = menubar.addMenu('没有卡密——帮助')
        
        # 关于选项
        about_action = QAction('关于软件', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 购买正版
        buy_action = QAction('购买正版', self)
        buy_action.triggered.connect(self.show_buy_info)
        help_menu.addAction(buy_action)
        
    def show_about(self):
        """显示关于信息"""
        about_text = f"""
        {APP_CONFIG['app']['title']} v{APP_CONFIG['app']['version']}
        
        作者：{APP_CONFIG['app']['author']}
        微信：{APP_CONFIG['app']['contact']}
        
        {APP_CONFIG['app']['copyright']}
        未经授权不得复制、分发或修改
        """
        
        QMessageBox.about(self, '关于软件', about_text)
        
    def show_buy_info(self):
        """显示购买信息"""
        buy_text = """
        【购买正版软件】
        
        1. 获取方式：
           - 添加作者微信：Hatebetray_
           - 备注：购买考试系统
        
        2. 正版特权：
           - 终身免费更新
           - 专属技术支持
           - 功能定制服务
        
        3. 温馨提示：
           - 使用正版，享受完整功能
           - 支持正版，打击盗版
           - 盗版软件可能含有病毒，请谨慎
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle('购买正版')
        msg.setText(buy_text)
        msg.setIcon(QMessageBox.Information)
        
        # 添加复制微信号按钮
        copy_btn = msg.addButton('复制微信号', QMessageBox.ActionRole)
        msg.addButton('关闭', QMessageBox.RejectRole)
        
        msg.exec_()
        
        if msg.clickedButton() == copy_btn:
            clipboard = QApplication.clipboard()
            clipboard.setText('Hatebetray_')
            QMessageBox.information(self, '提示', '微信号已复制到剪贴板！')

def main():
    try:
        # 设置异常钩子
        def exception_hook(exctype, value, traceback):
            print(f'An exception has occurred: {exctype.__name__}: {str(value)}')
            sys.__excepthook__(exctype, value, traceback)
        sys.excepthook = exception_hook
        
        # 设置高DPI支持 - 必须在创建QApplication之前
        if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
            QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
            QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        
        # 启动应用
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # 使用Fusion风格，更稳定
        
        # 设置应用程序属性
        app.setApplicationName("考试刷题系统")
        app.setApplicationVersion("2.1.3")
        app.setOrganizationName("记得晚安")
        
        # 设置全局字体
        font = app.font()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(10)
        app.setFont(font)
        
        exam = ExamSystem()
        exam.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    # 添加必要的导入
    from PyQt5 import QtCore
    main()