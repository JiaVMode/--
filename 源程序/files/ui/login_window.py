##########################################
#            注册登陆界面ui
#             作者：李嘉
#           学号：3123009043
#          班级：23人工智能1班
#         指导教师：苏畅、李剑锋
###########################################
"""
登录注册窗口
"""

import sys
import json
import os
import hashlib
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QStackedWidget, QMessageBox, QFrame, QTabWidget, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap

# 导入窗口模块
from .admin_window import AdminWindow
from .user_window import UserWindow

class LoginWindow(QWidget):
    def __init__(self, file_system):
        super().__init__()
        self.file_system = file_system
        self.users = self.load_users()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('虚拟文件管理器 - 登录')
        self.setGeometry(300, 100, 600, 700)
        # 不设置固定尺寸，允许拉伸
        # self.setFixedSize(600, 700)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'applications-system.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(40)
        
        # 标题
        title_label = QLabel('虚拟文件管理器')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 36px; font-weight: bold; color: #2c3e50; margin-bottom: 40px;')
        layout.addWidget(title_label)
        
        # 创建堆叠窗口用于切换登录和注册
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.stacked_widget, stretch=1)
        
        # 创建登录页面
        self.create_login_page()
        
        # 创建注册页面
        self.create_register_page()
        
        # 默认显示登录页面
        self.stacked_widget.setCurrentIndex(0)
        
        # 关于信息
        about_label = QLabel('操作系统课程设计项目')
        about_label.setAlignment(Qt.AlignCenter)
        about_label.setStyleSheet('color: #7f8c8d; font-size: 16px; margin-top: 40px;')
        layout.addWidget(about_label)
        
        layout.addStretch(1)
        self.setLayout(layout)
        
        # 设置样式
        self.setStyleSheet('''
            QWidget {
                background-color: #ecf0f1;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
            QLineEdit {
                padding: 16px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 2.5px solid #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        ''')
        
    def create_login_page(self):
        """创建登录页面"""
        login_widget = QWidget()
        layout = QVBoxLayout(login_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # 用户名输入框
        username_label = QLabel('用户名:')
        username_label.setStyleSheet('font-size: 18px; color: #2c3e50;')
        layout.addWidget(username_label)
        
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText('请输入用户名')
        self.login_username.setMinimumHeight(50)
        self.login_username.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 12px;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 2.5px solid #3498db;
            }
        """)
        layout.addWidget(self.login_username)
        
        # 密码输入框
        password_label = QLabel('密码:')
        password_label.setStyleSheet('font-size: 18px; color: #2c3e50;')
        layout.addWidget(password_label)
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText('请输入密码')
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setMinimumHeight(50)
        self.login_password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 12px;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 2.5px solid #3498db;
            }
        """)
        layout.addWidget(self.login_password)
        
        # 登录按钮
        login_button = QPushButton('登录')
        login_button.setMinimumHeight(55)
        login_button.clicked.connect(self.login)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        layout.addWidget(login_button)
        
        layout.addStretch()
        
        # 注册链接 - 改为纯文字
        register_layout = QHBoxLayout()
        register_layout.addStretch()
        register_link = QLabel('没有账号？去注册')
        register_link.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-size: 16px;
                text-decoration: underline;
            }
        """)
        register_link.setCursor(Qt.PointingHandCursor)
        register_link.mousePressEvent = lambda event: self.stacked_widget.setCurrentIndex(1)
        register_layout.addWidget(register_link)
        layout.addLayout(register_layout)
        
        self.stacked_widget.addWidget(login_widget)
        
    def create_register_page(self):
        """创建注册页面"""
        register_widget = QWidget()
        layout = QVBoxLayout(register_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # 用户名输入框
        username_label = QLabel('用户名:')
        username_label.setStyleSheet('font-size: 18px; color: #2c3e50;')
        layout.addWidget(username_label)
        
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText('请输入用户名')
        self.register_username.setMinimumHeight(50)
        self.register_username.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 12px;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 2.5px solid #3498db;
            }
        """)
        layout.addWidget(self.register_username)
        
        # 密码输入框
        password_label = QLabel('密码:')
        password_label.setStyleSheet('font-size: 18px; color: #2c3e50;')
        layout.addWidget(password_label)
        
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText('请输入密码（至少6位）')
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_password.setMinimumHeight(50)
        self.register_password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 12px;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 2.5px solid #3498db;
            }
        """)
        layout.addWidget(self.register_password)
        
        # 确认密码输入框
        confirm_label = QLabel('确认密码:')
        confirm_label.setStyleSheet('font-size: 18px; color: #2c3e50;')
        layout.addWidget(confirm_label)
        
        self.register_confirm_password = QLineEdit()
        self.register_confirm_password.setPlaceholderText('请再次输入密码')
        self.register_confirm_password.setEchoMode(QLineEdit.Password)
        self.register_confirm_password.setMinimumHeight(50)
        self.register_confirm_password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 12px;
                font-size: 18px;
            }
            QLineEdit:focus {
                border: 2.5px solid #3498db;
            }
        """)
        layout.addWidget(self.register_confirm_password)
        
        # 注册按钮
        register_button = QPushButton('注册')
        register_button.setMinimumHeight(55)
        register_button.clicked.connect(self.register)
        register_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        layout.addWidget(register_button)
        
        layout.addStretch()
        
        # 返回登录链接 - 改为纯文字
        back_layout = QHBoxLayout()
        back_layout.addStretch()
        back_link = QLabel('已有账号？去登录')
        back_link.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-size: 16px;
                text-decoration: underline;
            }
        """)
        back_link.setCursor(Qt.PointingHandCursor)
        back_link.mousePressEvent = lambda event: self.stacked_widget.setCurrentIndex(0)
        back_layout.addWidget(back_link)
        layout.addLayout(back_layout)
        
        self.stacked_widget.addWidget(register_widget)
        
    def load_users(self):
        """加载用户数据"""
        try:
            users_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 创建默认用户数据
                default_users = {
                    "admin": {
                        "password": "admin123",
                        "role": "admin",
                        "created_time": "2024-01-01 00:00:00",
                        "status": "active"
                    },
                    "user1": {
                        "password": "user123",
                        "role": "user",
                        "created_time": "2024-01-01 00:00:00",
                        "status": "active"
                    }
                }
                self.save_users(default_users)
                return default_users
        except Exception as e:
            print(f"加载用户数据失败: {e}")
            return {}
            
    def save_users(self, users=None):
        """保存用户数据"""
        if users is None:
            users = self.users
            
        try:
            users_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
            os.makedirs(os.path.dirname(users_file), exist_ok=True)
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户数据失败: {e}")
    
    def hash_password(self, password):
        """密码加密"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_password(self, input_password, stored_password):
        """验证密码"""
        # 使用SHA256哈希验证密码
        hashed_input = hashlib.sha256(input_password.encode()).hexdigest()
        return hashed_input == stored_password
    
    def login(self):
        """登录验证"""
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        if not username or not password:
            QMessageBox.warning(self, '错误', '请输入用户名和密码')
            return
            
        # 验证用户
        if username in self.users:
            user_info = self.users[username]
            # 使用文件系统的密码验证方法（支持哈希密码）
            if self.file_system.verify_user_password(username, password) and user_info.get('status') == 'active':
                # 登录成功
                if username == "admin" and self.verify_password(password, user_info.get('password', '')):
                    self.admin_window = AdminWindow(self.file_system)
                    self.admin_window.show()
                    self.close()
                else:
                    self.open_user_window(username)
            else:
                QMessageBox.warning(self, '错误', '密码错误或账户已被禁用')
        else:
            QMessageBox.warning(self, '错误', '用户不存在')
    
    def open_user_window(self, username):
        """打开用户窗口"""
        # 隐藏登录窗口
        self.hide()
        
        # 创建并显示用户窗口
        self.user_window = UserWindow(username, self.file_system)
        self.user_window.show()
        
        # 连接用户窗口关闭信号
        self.user_window.destroyed.connect(self.on_user_window_closed)
    
    def on_user_window_closed(self):
        """用户窗口关闭时的处理"""
        # 清空登录信息
        self.login_username.clear()
        self.login_password.clear()
        
        # 显示登录窗口
        self.show()
    
    def register(self):
        """注册功能"""
        username = self.register_username.text().strip()
        password = self.register_password.text().strip()
        confirm = self.register_confirm_password.text().strip()
        
        if not username or not password or not confirm:
            QMessageBox.warning(self, '提示', '请填写所有字段')
            return
        
        if password != confirm:
            QMessageBox.warning(self, '错误', '两次输入的密码不一致')
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, '错误', '密码长度至少6位')
            return
        
        # 检查用户名是否已存在
        if username in self.users:
            QMessageBox.warning(self, '错误', '用户名已存在')
            return
        
        # 添加新用户（使用哈希密码）
        import hashlib
        from datetime import datetime
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        self.users[username] = {
            "password": hashed_password,
            "role": "user",
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active"
        }
        self.save_users()
        
        # 自动创建用户目录
        self.file_system.create_user_directory(username)
        
        QMessageBox.information(self, '成功', '注册成功！请返回登录')
        
        # 清空输入框
        self.register_username.clear()
        self.register_password.clear()
        self.register_confirm_password.clear()
        
        # 切换到登录页面
        self.stacked_widget.setCurrentIndex(0)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName('虚拟文件管理器')
    app.setApplicationVersion('1.0')
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    window = LoginWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 