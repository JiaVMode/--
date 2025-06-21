import json
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QComboBox, QMessageBox, QHeaderView, QGroupBox,
                             QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class UserManagementDialog(QDialog):
    """用户管理对话框"""
    user_updated = pyqtSignal()  # 用户信息更新信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.users_file = "data/users.json"
        self.users = self.load_users()
        self.init_ui()
        self.load_user_list()
        
    def init_ui(self):
        self.setWindowTitle("用户管理")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # 用户列表
        group_list = QGroupBox("用户列表")
        list_layout = QVBoxLayout()
        
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["用户名", "角色", "创建时间", "状态"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.itemSelectionChanged.connect(self.on_user_selected)
        
        list_layout.addWidget(self.user_table)
        group_list.setLayout(list_layout)
        
        # 用户操作按钮
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加用户")
        self.btn_edit = QPushButton("编辑用户")
        self.btn_delete = QPushButton("删除用户")
        self.btn_reset_pwd = QPushButton("重置密码")
        
        self.btn_add.clicked.connect(self.add_user)
        self.btn_edit.clicked.connect(self.edit_user)
        self.btn_delete.clicked.connect(self.delete_user)
        self.btn_reset_pwd.clicked.connect(self.reset_password)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_reset_pwd)
        btn_layout.addStretch()
        
        # 关闭按钮
        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addWidget(group_list)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def load_users(self):
        """加载用户数据"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
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
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户数据失败: {e}")
            
    def load_user_list(self):
        """加载用户列表到表格"""
        self.user_table.setRowCount(0)
        for username, user_info in self.users.items():
            row = self.user_table.rowCount()
            self.user_table.insertRow(row)
            
            self.user_table.setItem(row, 0, QTableWidgetItem(username))
            self.user_table.setItem(row, 1, QTableWidgetItem(user_info.get('role', 'user')))
            self.user_table.setItem(row, 2, QTableWidgetItem(user_info.get('created_time', '')))
            self.user_table.setItem(row, 3, QTableWidgetItem(user_info.get('status', 'active')))
            
    def on_user_selected(self):
        """用户选择变化"""
        selected_rows = self.user_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        self.btn_reset_pwd.setEnabled(has_selection)
        
    def get_selected_username(self):
        """获取选中的用户名"""
        selected_rows = self.user_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            return self.user_table.item(row, 0).text()
        return None
        
    def add_user(self):
        """添加用户"""
        dialog = UserEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            username = dialog.username_edit.text().strip()
            password = dialog.password_edit.text()
            role = dialog.role_combo.currentText()
            
            if not username:
                QMessageBox.warning(self, "错误", "用户名不能为空")
                return
                
            if username in self.users:
                QMessageBox.warning(self, "错误", "用户名已存在")
                return
                
            # 添加新用户（使用哈希密码）
            import hashlib
            from datetime import datetime
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            self.users[username] = {
                "password": hashed_password,
                "role": role,
                "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "active"
            }
            
            self.save_users()
            self.load_user_list()
            self.user_updated.emit()
            QMessageBox.information(self, "成功", f"用户 {username} 创建成功")
            
    def edit_user(self):
        """编辑用户"""
        username = self.get_selected_username()
        if not username:
            return
            
        if username == "admin":
            QMessageBox.warning(self, "错误", "不能编辑管理员账户")
            return
            
        user_info = self.users[username]
        dialog = UserEditDialog(self, username, user_info)
        
        if dialog.exec_() == QDialog.Accepted:
            new_username = dialog.username_edit.text().strip()
            password = dialog.password_edit.text()
            role = dialog.role_combo.currentText()
            
            if not new_username:
                QMessageBox.warning(self, "错误", "用户名不能为空")
                return
                
            if new_username != username and new_username in self.users:
                QMessageBox.warning(self, "错误", "用户名已存在")
                return
                
            # 更新用户信息（使用哈希密码）
            import hashlib
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            
            if new_username != username:
                # 用户名改变，需要删除旧用户并创建新用户
                del self.users[username]
                self.users[new_username] = {
                    "password": hashed_password,
                    "role": role,
                    "created_time": user_info.get('created_time', ''),
                    "status": user_info.get('status', 'active')
                }
            else:
                # 只更新密码和角色
                self.users[username]["password"] = hashed_password
                self.users[username]["role"] = role
                
            self.save_users()
            self.load_user_list()
            self.user_updated.emit()
            QMessageBox.information(self, "成功", f"用户信息更新成功")
            
    def delete_user(self):
        """删除用户"""
        username = self.get_selected_username()
        if not username:
            return
            
        if username == "admin":
            QMessageBox.warning(self, "错误", "不能删除管理员账户")
            return
            
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除用户 {username} 吗？\n此操作不可恢复！",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            del self.users[username]
            self.save_users()
            self.load_user_list()
            self.user_updated.emit()
            QMessageBox.information(self, "成功", f"用户 {username} 已删除")
            
    def reset_password(self):
        """重置密码"""
        username = self.get_selected_username()
        if not username:
            return
            
        from PyQt5.QtWidgets import QInputDialog
        new_password, ok = QInputDialog.getText(self, "重置密码", 
                                              f"请输入用户 {username} 的新密码：",
                                              QLineEdit.Password)
        
        if ok and new_password:
            import hashlib
            hashed_password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            self.users[username]["password"] = hashed_password
            self.save_users()
            QMessageBox.information(self, "成功", f"用户 {username} 密码已重置")


class UserEditDialog(QDialog):
    """用户编辑对话框"""
    def __init__(self, parent=None, username="", user_info=None):
        super().__init__(parent)
        self.username = username
        self.user_info = user_info or {}
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("编辑用户" if self.username else "添加用户")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        # 表单
        form_layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setText(self.username)
        if self.username == "admin":
            self.username_edit.setEnabled(False)
        form_layout.addRow("用户名:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setText(self.user_info.get('password', ''))
        form_layout.addRow("密码:", self.password_edit)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        current_role = self.user_info.get('role', 'user')
        index = self.role_combo.findText(current_role)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)
        if self.username == "admin":
            self.role_combo.setEnabled(False)
        form_layout.addRow("角色:", self.role_combo)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout) 