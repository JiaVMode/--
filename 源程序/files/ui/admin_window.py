##########################################
#             管理员窗口
#             作者：李嘉
#           学号：3123009043
#          班级：23人工智能1班
#         指导教师：苏畅、李剑锋
###########################################
"""
管理员主窗口 - 基于JSON文件系统 (已重构)
"""

import sys
import os
import json
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QMessageBox,
                             QToolBar, QAction, QStatusBar, QMenuBar, QMenu,
                             QListWidget, QListWidgetItem, QSplitter, QTreeWidget,
                             QTreeWidgetItem, QLineEdit, QInputDialog, QDialog,
                             QTextEdit, QDialogButtonBox, QTableWidget, QTableWidgetItem,
                             QFileDialog, QSizePolicy, QFormLayout, QCheckBox, QSpinBox,
                             QGroupBox, QTabWidget)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap

# 导入文件系统
from core.file_system import FileSystem
from ui.user_management_dialog import UserManagementDialog
from .system_monitor_dialog import SystemMonitorDialog

class AdminWindow(QMainWindow):
    def __init__(self, file_system):
        super().__init__()
        self.file_system = file_system
        self.username = "admin"
        self.current_path = "/"
        self.clipboard = []
        self.clipboard_mode = None  # 'copy' or 'cut'
        self.show_hidden_files = False
        self.current_sort_key = 'name'  # 当前排序键
        self.current_sort_order = 'asc'  # 当前排序顺序：'asc' 或 'desc'
        self.icon_provider = {
            'dir': QIcon(os.path.join(self.file_system.data_dir, 'folder.png')),
            'file': QIcon(os.path.join(self.file_system.data_dir, 'text-x-generic.png')),
            'unknown': QIcon(os.path.join(self.file_system.data_dir, 'unknown.png'))
        }
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"文件管理器 - 管理员 ({self.username})")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), '..', 'data', 'applications-system.png')))
        
        self.create_menu_bar()
        self.create_toolbar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 地址栏和搜索框
        top_layout = QHBoxLayout()
        
        # 地址栏
        address_layout = QHBoxLayout()
        self.address_edit = QLineEdit()
        # 设置初始路径为用户主目录，而不是文件所在目录
        user_home = f"/home/{self.username}"
        self.address_edit.setText(user_home)
        self.address_edit.returnPressed.connect(self.navigate_from_address_bar)
        address_layout.addWidget(QLabel("地址:"))
        address_layout.addWidget(self.address_edit)
        top_layout.addLayout(address_layout)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索文件或文件夹...")
        self.search_edit.returnPressed.connect(self.search_files)
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addWidget(self.search_edit)
        
        self.search_button = QPushButton("搜索")
        self.search_button.clicked.connect(self.search_files)
        search_layout.addWidget(self.search_button)
        
        top_layout.addLayout(search_layout)
        main_layout.addLayout(top_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["目录"])
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        splitter.addWidget(self.tree_widget)
        
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ListMode)
        self.list_widget.setIconSize(QSize(32, 32))
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.itemDoubleClicked.connect(self.on_list_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        splitter.addWidget(self.list_widget)
        
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)
        
        self.setStatusBar(QStatusBar())
        
        self.load_tree_structure()
        self.load_directory(self.current_path)

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        file_menu.addAction('新建文件夹', self.create_new_folder)
        file_menu.addAction('新建文件', self.create_new_file)
        file_menu.addSeparator()
        file_menu.addAction('退出', self.close)

        manage_menu = menubar.addMenu('管理')
        manage_menu.addAction('用户管理', self.open_user_management)

        view_menu = menubar.addMenu('视图')
        view_menu.addAction('刷新', self.refresh_view)
        view_menu.addAction('统计信息', self.show_statistics)
        
        # 排序菜单
        sort_menu = self.menuBar().addMenu("排序")
        
        # 按名称排序
        sort_name_menu = QMenu("按名称", self)
        sort_name_asc = QAction("升序", self)
        sort_name_asc.triggered.connect(lambda: self.sort_items('name', 'asc'))
        sort_name_desc = QAction("降序", self)
        sort_name_desc.triggered.connect(lambda: self.sort_items('name', 'desc'))
        sort_name_menu.addAction(sort_name_asc)
        sort_name_menu.addAction(sort_name_desc)
        sort_menu.addMenu(sort_name_menu)
        
        # 按大小排序
        sort_size_menu = QMenu("按大小", self)
        sort_size_asc = QAction("升序", self)
        sort_size_asc.triggered.connect(lambda: self.sort_items('size', 'asc'))
        sort_size_desc = QAction("降序", self)
        sort_size_desc.triggered.connect(lambda: self.sort_items('size', 'desc'))
        sort_size_menu.addAction(sort_size_asc)
        sort_size_menu.addAction(sort_size_desc)
        sort_menu.addMenu(sort_size_menu)
        
        # 按类型排序
        sort_type_menu = QMenu("按类型", self)
        sort_type_asc = QAction("升序", self)
        sort_type_asc.triggered.connect(lambda: self.sort_items('type', 'asc'))
        sort_type_desc = QAction("降序", self)
        sort_type_desc.triggered.connect(lambda: self.sort_items('type', 'desc'))
        sort_type_menu.addAction(sort_type_asc)
        sort_type_menu.addAction(sort_type_desc)
        sort_menu.addMenu(sort_type_menu)
        
        # 按修改时间排序
        sort_time_menu = QMenu("按修改时间", self)
        sort_time_asc = QAction("升序", self)
        sort_time_asc.triggered.connect(lambda: self.sort_items('modified', 'asc'))
        sort_time_desc = QAction("降序", self)
        sort_time_desc.triggered.connect(lambda: self.sort_items('modified', 'desc'))
        sort_time_menu.addAction(sort_time_asc)
        sort_time_menu.addAction(sort_time_desc)
        sort_menu.addMenu(sort_time_menu)

        # 系统监控菜单
        monitor_menu = self.menuBar().addMenu("系统监控")
        monitor_menu.addAction("系统监控", self.show_system_monitor)

        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助")
        help_menu.addAction("系统信息", self.show_system_info)
        help_menu.addAction("关于", self.show_about)

    def create_toolbar(self):
        toolbar = self.addToolBar('主工具栏')
        toolbar.addAction(QIcon.fromTheme("go-previous", QIcon(os.path.join(self.file_system.data_dir, 'go-up.png'))), "上一级", self.go_up)
        toolbar.addSeparator()
        toolbar.addAction(QIcon.fromTheme("folder-new", QIcon(os.path.join(self.file_system.data_dir, 'folder-new.png'))), "新建文件夹", self.create_new_folder)
        toolbar.addAction(QIcon.fromTheme("document-new", QIcon(os.path.join(self.file_system.data_dir, 'document-new.png'))), "新建文件", self.create_new_file)
        toolbar.addSeparator()
        toolbar.addAction(QIcon.fromTheme("edit-copy", QIcon(os.path.join(self.file_system.data_dir, 'edit-copy.png'))), "复制", self.toolbar_copy)
        toolbar.addAction(QIcon.fromTheme("edit-cut", QIcon(os.path.join(self.file_system.data_dir, 'edit-cut.png'))), "剪切", self.toolbar_cut)
        toolbar.addAction(QIcon.fromTheme("edit-paste", QIcon(os.path.join(self.file_system.data_dir, 'edit-paste.png'))), "粘贴", self.toolbar_paste)
        toolbar.addSeparator()
        toolbar.addAction(QIcon.fromTheme("edit-delete", QIcon(os.path.join(self.file_system.data_dir, 'edit-delete.png'))), "删除", self.toolbar_delete)
        toolbar.addAction(QIcon.fromTheme("edit-rename", QIcon(os.path.join(self.file_system.data_dir, 'edit-rename.png'))), "重命名", self.toolbar_rename)
        toolbar.addSeparator()
        toolbar.addAction(QIcon.fromTheme("view-refresh", QIcon(os.path.join(self.file_system.data_dir, 'view-refresh.png'))), "刷新", self.refresh_view)

    def load_tree_structure(self):
        self.tree_widget.clear()
        full_tree = self.file_system.get_full_tree()
        root_node = full_tree.get('root')
        if not root_node: return

        root_item = QTreeWidgetItem(self.tree_widget, [root_node.get('name', '/')])
        root_item.setData(0, Qt.UserRole, root_node)
        root_item.setIcon(0, self.icon_provider['dir'])
        
        self._add_tree_items_recursive(root_item, root_node.get('children', []))
        self.tree_widget.expandItem(root_item)

    def _add_tree_items_recursive(self, parent_item, children_nodes):
        sorted_children = sorted(children_nodes, key=lambda x: x['name'])
        for node in sorted_children:
            if node.get('type') == 'dir':
                child_item = QTreeWidgetItem(parent_item, [node.get('name')])
                child_item.setData(0, Qt.UserRole, node)
                child_item.setIcon(0, self.icon_provider['dir'])
                self._add_tree_items_recursive(child_item, node.get('children', []))

    def load_directory(self, path):
        self.list_widget.clear()
        self.current_path = path
        self.address_edit.setText(path)
        
        content = self.file_system.get_directory_content(path, self.username, self.show_hidden_files)
        if content is None: return

        sorted_content = sorted(content, key=lambda x: (x['type'] != 'dir', x['name']))
        for item_data in sorted_content:
            # 构建显示名称：文件名 + 修改时间 + 大小（仅文件）
            display_name = item_data['name']
            
            # 添加修改时间
            modified_time = item_data.get('modified', '未知时间')
            display_name += f" - {modified_time}"
            
            # 添加文件大小（仅文件）
            if item_data['type'] == 'file':
                size = item_data.get('size', 0)
                size_str = self.format_file_size(size)
                display_name += f" - {size_str}"
            
            list_item = QListWidgetItem(display_name)
            list_item.setData(Qt.UserRole, item_data)
            list_item.setIcon(self.icon_provider.get(item_data['type'], self.icon_provider['unknown']))
            self.list_widget.addItem(list_item)
        self.statusBar().showMessage(f"共 {len(sorted_content)} 项")

    # --- Event Handlers and Actions ---

    def on_tree_item_clicked(self, item, column):
        item_data = item.data(0, Qt.UserRole)
        if item_data and 'path' in item_data:
            self.load_directory(item_data['path'])

    def on_list_item_double_clicked(self, item):
        item_data = item.data(Qt.UserRole)
        if item_data['type'] == 'dir':
            self.load_directory(item_data['path'])
        else: # file
            self.open_file(item_data)

    def navigate_from_address_bar(self):
        path = self.address_edit.text()
        self.load_directory(path)

    def go_up(self):
        if self.current_path != '/':
            parent_path = os.path.dirname(self.current_path).replace('\\', '/')
            self.load_directory(parent_path)

    def refresh_view(self):
        self.load_tree_structure()
        self.load_directory(self.current_path)
        self.statusBar().showMessage('视图已刷新', 2000)

    def create_new_file(self):
        name, ok = QInputDialog.getText(self, '新建文件', '请输入文件名:')
        if ok and name:
            self.file_system.create_file(self.current_path, name, "", self.username)
            self.refresh_view()

    def create_new_folder(self):
        name, ok = QInputDialog.getText(self, '新建文件夹', '请输入文件夹名:')
        if ok and name:
            self.file_system.create_directory(self.current_path, name, self.username)
            self.refresh_view()

    def open_file(self, item_data):
        content = self.file_system.get_file_content(item_data['path'], self.username)
        # 创建非模态文件编辑对话框
        self.file_edit_dialog = FileEditDialog(item_data, content, self.file_system, self, self.username)
        self.file_edit_dialog.show()

    def open_user_management(self):
        """打开用户管理对话框"""
        dialog = UserManagementDialog(self)
        dialog.user_updated.connect(self.on_users_updated)
        dialog.exec_()
        
    def on_users_updated(self):
        """用户信息更新后的处理"""
        QMessageBox.information(self, "提示", "用户信息已更新，请重新登录以应用更改。")

    def show_system_info(self):
        """显示系统信息"""
        import platform
        import datetime
        
        info = f"""
系统信息:
操作系统: {platform.system()} {platform.release()}
Python版本: {platform.python_version()}
当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
登录用户: {self.username}
用户角色: 管理员
文件系统: JSON文件系统
        """
        
        QMessageBox.information(self, '系统信息', info.strip())

    def show_system_monitor(self):
        """显示系统监控对话框"""
        # 创建非模态对话框
        self.monitor_dialog = SystemMonitorDialog(self.file_system, self.file_system.system_monitor, self)
        self.monitor_dialog.show()

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "虚拟文件管理器 v1.0\n\n"
                         "学生：李嘉\n"
                         "学号：3123009043\n"
                         "班级：23人工智能1班\n\n"
                         "指导教师：苏畅、李剑锋\n\n"
                         "操作系统课程设计")

    # --- Context Menu and Actions ---

    def show_context_menu(self, position):
        menu = QMenu()
        selected_items = self.list_widget.selectedItems()

        if selected_items:
            menu.addAction("打开", self.context_open)
            menu.addAction("重命名", self.context_rename)
            menu.addSeparator()
            menu.addAction("剪切", self.context_cut)
            menu.addAction("复制", self.context_copy)
            menu.addSeparator()
            menu.addAction("删除", self.context_delete)
            menu.addSeparator()
            
            # 添加隐藏/显示选项
            item_data = selected_items[0].data(Qt.UserRole)
            if item_data.get('hidden', False):
                menu.addAction("显示", self.context_show_item)
            else:
                menu.addAction("隐藏", self.context_hide_item)
            
            menu.addSeparator()
            menu.addAction("属性", self.context_properties)
        else:
            menu.addAction("新建文件夹", self.create_new_folder)
            menu.addAction("新建文件", self.create_new_file)

        # 添加显示隐藏文件的选项
        menu.addSeparator()
        show_hidden_action = menu.addAction("显示隐藏文件", self.toggle_show_hidden)
        show_hidden_action.setCheckable(True)
        show_hidden_action.setChecked(self.show_hidden_files)

        paste_action = menu.addAction("粘贴", self.context_paste)
        paste_action.setEnabled(bool(self.file_system.get_clipboard_info().get('type')))
        
        menu.exec_(self.list_widget.mapToGlobal(position))

    def get_selected_items_data(self):
        return [item.data(Qt.UserRole) for item in self.list_widget.selectedItems()]

    def context_open(self):
        selected_data = self.get_selected_items_data()
        if not selected_data: return
        self.on_list_item_double_clicked(self.list_widget.selectedItems()[0])

    def context_rename(self):
        selected_data = self.get_selected_items_data()
        if not selected_data or len(selected_data) != 1: 
            QMessageBox.information(self, "重命名", "请选择一个项目进行重命名")
            return
        item_data = selected_data[0]
        
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=item_data['name'])
        if ok and new_name and new_name != item_data['name']:
            self.file_system.rename_item(self.current_path, item_data['name'], new_name, item_data['type'], self.username)
            self.refresh_view()

    def context_delete(self):
        selected_data = self.get_selected_items_data()
        if not selected_data: return
        
        # 检查是否包含受保护的目录
        protected_items = []
        for item_data in selected_data:
            if item_data['name'] == 'home' and self.current_path == '/':
                protected_items.append('/home')
            elif item_data['name'] == 'root' and self.current_path == '/':
                protected_items.append('/root')
        
        if protected_items:
            QMessageBox.warning(self, "删除失败", f"以下系统目录不允许删除：\n{', '.join(protected_items)}")
            return
        
        reply = QMessageBox.question(self, '确认删除', f"确定要删除 {len(selected_data)} 个项目吗?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for item_data in selected_data:
                self.file_system.delete_item(self.current_path, item_data['name'], item_data['type'], self.username)
            self.refresh_view()

    def context_cut(self):
        selected_data = self.get_selected_items_data()
        if selected_data:
            self.file_system.cut_items(self.current_path, selected_data, self.username)

    def context_copy(self):
        selected_data = self.get_selected_items_data()
        if selected_data:
            self.file_system.copy_items(self.current_path, selected_data, self.username)

    def context_paste(self):
        self.file_system.paste_items(self.current_path, self.username)
        self.refresh_view()

    def context_properties(self):
        selected_data = self.get_selected_items_data()
        if not selected_data or len(selected_data) != 1:
            QMessageBox.information(self, "属性", "请选择一个项目查看属性")
            return
        item_data = selected_data[0]
        if item_data['type'] == 'dir':
            self.properties_dialog = FolderPropertiesDialog(item_data, self.file_system, self)
        else:
            self.properties_dialog = FilePropertiesDialog(item_data, self.file_system, self)
        self.properties_dialog.show()

    def context_hide_item(self):
        """隐藏选中的项目"""
        selected_data = self.get_selected_items_data()
        if not selected_data: return
        for item_data in selected_data:
            self.file_system.hide_item(self.current_path, item_data['name'], item_data['type'], self.username)
        self.refresh_view()

    def context_show_item(self):
        """显示选中的项目"""
        selected_data = self.get_selected_items_data()
        if not selected_data: return
        for item_data in selected_data:
            self.file_system.unhide_item(self.current_path, item_data['name'], item_data['type'], self.username)
        self.refresh_view()

    def toggle_show_hidden(self):
        """切换显示隐藏文件"""
        self.show_hidden_files = not self.show_hidden_files
        self.refresh_view()

    # --- Toolbar Actions ---
    def toolbar_copy(self):
        """工具栏复制按钮"""
        selected_data = self.get_selected_items_data()
        if not selected_data:
            QMessageBox.information(self, "提示", "请先选择要复制的项目")
            return
        self.context_copy()

    def toolbar_cut(self):
        """工具栏剪切按钮"""
        selected_data = self.get_selected_items_data()
        if not selected_data:
            QMessageBox.information(self, "提示", "请先选择要剪切的项目")
            return
        self.context_cut()

    def toolbar_paste(self):
        """工具栏粘贴按钮"""
        if not self.file_system.get_clipboard_info().get('type'):
            QMessageBox.information(self, "提示", "剪贴板为空")
            return
        self.context_paste()

    def toolbar_delete(self):
        """工具栏删除按钮"""
        selected_data = self.get_selected_items_data()
        if not selected_data:
            QMessageBox.information(self, "提示", "请先选择要删除的项目")
            return
        self.context_delete()

    def toolbar_rename(self):
        """工具栏重命名按钮"""
        selected_data = self.get_selected_items_data()
        if not selected_data or len(selected_data) != 1:
            QMessageBox.information(self, "提示", "请选择一个项目进行重命名")
            return
        self.context_rename()

    def search_files(self):
        """搜索文件功能"""
        search_text = self.search_edit.text().strip()
        if not search_text:
            self.refresh_view()
            return
        
        # 清空当前列表
        self.list_widget.clear()
        
        # 递归搜索
        results = self._search_recursive(self.current_path, search_text)
        
        # 显示搜索结果
        for item_data in results:
            # 构建显示名称：文件名 + 修改时间 + 大小（仅文件）
            display_name = item_data['name']
            
            # 添加修改时间
            modified_time = item_data.get('modified', '未知时间')
            display_name += f" - {modified_time}"
            
            # 添加文件大小（仅文件）
            if item_data['type'] == 'file':
                size = item_data.get('size', 0)
                size_str = self.format_file_size(size)
                display_name += f" - {size_str}"
            
            # 添加文件路径
            display_name += f" ({item_data['path']})"
            
            list_item = QListWidgetItem(display_name)
            list_item.setData(Qt.UserRole, item_data)
            list_item.setIcon(self.icon_provider.get(item_data['type'], self.icon_provider['unknown']))
            
            # 高亮显示匹配的文件
            if search_text.lower() in item_data['name'].lower():
                font = list_item.font()
                font.setBold(True)
                list_item.setFont(font)
            
            self.list_widget.addItem(list_item)
        
        self.statusBar().showMessage(f"搜索结果：共找到 {len(results)} 项")
        
    def _search_recursive(self, path, search_text):
        """递归搜索文件和文件夹"""
        results = []
        content = self.file_system.get_directory_content(path, self.username, True)  # 显示隐藏文件
        
        if not content:
            return results
            
        for item in content:
            # 检查当前项是否匹配
            if search_text.lower() in item['name'].lower():
                results.append(item)
            
            # 如果是目录，递归搜索
            if item['type'] == 'dir':
                sub_results = self._search_recursive(item['path'], search_text)
                results.extend(sub_results)
        
        return results

    def show_statistics(self):
        """显示统计信息"""
        content = self.file_system.get_directory_content(self.current_path, self.username, self.show_hidden_files)
        if not content:
            QMessageBox.information(self, "统计信息", "当前目录为空")
            return
            
        # 统计信息
        total_items = len(content)
        files = [item for item in content if item['type'] == 'file']
        folders = [item for item in content if item['type'] == 'dir']
        hidden_items = [item for item in content if item.get('hidden', False)]
        
        # 计算文件总大小
        total_size = sum(item.get('size', 0) for item in files)
        
        # 格式化大小
        def format_size(size_bytes):
            if size_bytes < 1024:
                return f"{size_bytes} 字节"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        
        # 构建统计信息文本
        stats_text = f"目录：{self.current_path}\n\n"
        stats_text += f"总项目数：{total_items}\n"
        stats_text += f"文件数量：{len(files)}\n"
        stats_text += f"文件夹数量：{len(folders)}\n"
        stats_text += f"隐藏项目：{len(hidden_items)}\n"
        stats_text += f"文件总大小：{format_size(total_size)}\n\n"
        
        # 文件类型统计
        if files:
            file_types = {}
            for file in files:
                name = file['name']
                if '.' in name:
                    ext = name.split('.')[-1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
                else:
                    file_types['无扩展名'] = file_types.get('无扩展名', 0) + 1
            
            stats_text += "文件类型统计：\n"
            for ext, count in sorted(file_types.items()):
                stats_text += f"  .{ext}：{count} 个\n"
        
        QMessageBox.information(self, "统计信息", stats_text)

    def sort_items(self, sort_key, sort_order='asc'):
        """排序功能"""
        self.current_sort_key = sort_key
        self.current_sort_order = sort_order
        
        content = self.file_system.get_directory_content(self.current_path, self.username, self.show_hidden_files)
        if not content:
            return
        
        # 根据排序键进行排序
        if sort_key == 'name':
            sorted_content = sorted(content, key=lambda x: x['name'].lower(), reverse=(sort_order == 'desc'))
        elif sort_key == 'size':
            sorted_content = sorted(content, key=lambda x: x.get('size', 0), reverse=(sort_order == 'desc'))
        elif sort_key == 'type':
            sorted_content = sorted(content, key=lambda x: (x['type'], x['name'].lower()), reverse=(sort_order == 'desc'))
        elif sort_key == 'modified':
            sorted_content = sorted(content, key=lambda x: x.get('modified', ''), reverse=(sort_order == 'desc'))
        else:
            sorted_content = content
        
        # 清空当前列表
        self.list_widget.clear()
        
        # 显示排序后的内容
        for item_data in sorted_content:
            # 构建显示名称：文件名 + 修改时间 + 大小（仅文件）
            display_name = item_data['name']
            
            # 添加修改时间
            modified_time = item_data.get('modified', '未知时间')
            display_name += f" - {modified_time}"
            
            # 添加文件大小（仅文件）
            if item_data['type'] == 'file':
                size = item_data.get('size', 0)
                size_str = self.format_file_size(size)
                display_name += f" - {size_str}"
            
            list_item = QListWidgetItem(display_name)
            list_item.setData(Qt.UserRole, item_data)
            list_item.setIcon(self.icon_provider.get(item_data['type'], self.icon_provider['unknown']))
            self.list_widget.addItem(list_item)
        
        order_text = "降序" if sort_order == 'desc' else "升序"
        self.statusBar().showMessage(f"已按{sort_key}{order_text}排序，共 {len(sorted_content)} 项")

    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} 字节"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def navigate_to_path(self):
        """导航到指定路径"""
        path = self.address_edit.text().strip()
        if path:
            # 管理员可以访问所有目录，但普通用户需要权限检查
            if self.current_user != 'admin' and not self.has_permission_to_access(path):
                QMessageBox.warning(self, '权限错误', f'您没有权限访问路径: {path}')
                # 重置为用户主目录
                user_home = f"/home/{self.current_user}"
                self.address_edit.setText(user_home)
                self.refresh_file_list(user_home)
                return
            self.refresh_file_list(path)
            
    def has_permission_to_access(self, path):
        """检查用户是否有权限访问指定路径"""
        # 检查路径是否为空或无效
        if not path or not isinstance(path, str):
            return False
            
        # 管理员可以访问所有目录
        if self.current_user == 'admin':
            return True
            
        # 用户总是可以访问自己的主目录
        user_home = f"/home/{self.current_user}"
        if path == user_home or path.startswith(user_home + '/'):
            return True
        
        # 用户可以访问共享目录
        if path == "/home/shared" or path.startswith("/home/shared/"):
            return True
        
        # 其他路径需要检查权限
        try:
            # 尝试获取目录内容来检查权限
            content = self.file_system.get_directory_content(path, self.current_user, False)
            return content is not None
        except:
            return False

    def refresh_file_list(self, path=None):
        """刷新文件列表"""
        if path is None:
            path = self.address_edit.text().strip()
        
        # 确保路径是有效的字符串，如果为空则使用用户主目录
        if not path or not isinstance(path, str):
            path = f"/home/{self.current_user}"
            self.address_edit.setText(path)
        
        self.file_list.clear()
        content = self.file_system.get_directory_content(path, self.current_user, True)
        
        if content:
            for item in sorted(content, key=lambda x: (x['type'] != 'dir', x['name'])):
                list_item = QListWidgetItem()
                list_item.setText(item['name'])
                list_item.setData(Qt.UserRole, item)
                
                # 设置图标
                if item['type'] == 'dir':
                    list_item.setIcon(self.parent().icon_provider['dir'])
                else:
                    list_item.setIcon(self.parent().icon_provider.get('file', self.parent().icon_provider['unknown']))
                
                self.file_list.addItem(list_item)

class FileEditDialog(QDialog):
    """文件编辑对话框"""
    def __init__(self, file_info, content, file_system, parent=None, current_user=None):
        super().__init__(parent)
        self.file_info = file_info
        self.file_system = file_system
        self.current_user = current_user
        self.original_content = content
        
        # 设置为非模态窗口
        self.setModal(False)
        
        self.setup_ui(content)
        
    def setup_ui(self, content):
        self.setWindowTitle(f'编辑 - {self.file_info["name"]}')
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout()
        
        # 文件信息
        info_label = QLabel(f"文件：{self.file_info['name']} | 路径：{self.file_info['path']}")
        info_label.setStyleSheet("QLabel { color: gray; }")
        layout.addWidget(info_label)
        
        # 文本编辑区域
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.textChanged.connect(self.mark_modified)
        layout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_file)
        button_layout.addWidget(save_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close_dialog)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 标记为未修改
        self.is_modified = False
        
    def mark_modified(self):
        """标记文件为已修改"""
        if not self.is_modified:
            self.is_modified = True
            self.setWindowTitle(f'编辑 - {self.file_info["name"]} *')
        
    def save_file(self):
        """保存文件"""
        new_content = self.text_edit.toPlainText()
        dir_path = os.path.dirname(self.file_info['path']).replace('\\', '/')
        if not dir_path: dir_path = '/'
        file_name = os.path.basename(self.file_info['path'])
        
        success = self.file_system.write_file(dir_path, file_name, new_content, self.current_user)
        if success:
            self.is_modified = False
            self.original_content = new_content
            self.setWindowTitle(f'编辑 - {self.file_info["name"]}')
            QMessageBox.information(self, '成功', '文件保存成功')
        else:
            QMessageBox.warning(self, '错误', '保存失败，可能因为权限不足')
            
    def close_dialog(self):
        """关闭对话框"""
        # 检查是否有未保存的更改
        if self.is_modified:
            reply = QMessageBox.question(self, "保存更改", 
                                       "文件已修改，是否保存？",
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
        
        self.reject()

class FolderPropertiesDialog(QDialog):
    """文件夹属性对话框"""
    def __init__(self, folder_data, file_system, parent=None):
        super().__init__(parent)
        self.folder_data = folder_data
        self.file_system = file_system
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f'文件夹属性 - {self.folder_data["name"]}')
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 文件夹图标和名称
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(os.path.join(os.path.dirname(__file__), '..', 'data', 'folder.png')).pixmap(48, 48))
        header_layout.addWidget(icon_label)
        
        name_label = QLabel(self.folder_data["name"])
        name_label.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 属性信息
        form_layout = QFormLayout()
        
        # 绝对路径
        path_label = QLabel(self.folder_data["path"])
        path_label.setWordWrap(True)
        form_layout.addRow('位置:', path_label)
        
        # 文件数量
        file_count = self.get_file_count()
        form_layout.addRow('包含文件:', QLabel(str(file_count)))
        
        # 文件夹数量
        folder_count = self.get_folder_count()
        form_layout.addRow('包含文件夹:', QLabel(str(folder_count)))
        
        # 总项目数
        total_count = file_count + folder_count
        form_layout.addRow('总项目数:', QLabel(str(total_count)))
        
        # 创建时间
        created_time = self.folder_data.get("created", "未知")
        form_layout.addRow('创建时间:', QLabel(created_time))
        
        # 修改时间
        modified_time = self.folder_data.get("modified", "未知")
        form_layout.addRow('修改时间:', QLabel(modified_time))
        
        layout.addLayout(form_layout)
        
        # 文件夹属性
        attributes_group = QWidget()
        attributes_layout = QVBoxLayout(attributes_group)
        
        self.is_hidden = QCheckBox('隐藏')
        self.is_hidden.setChecked(self.folder_data.get('hidden', False))
        attributes_layout.addWidget(self.is_hidden)
        
        layout.addWidget(attributes_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.save_properties)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def save_properties(self):
        """保存属性设置"""
        # 保存隐藏状态
        new_hidden = self.is_hidden.isChecked()
        if new_hidden != self.folder_data.get('hidden', False):
            path = os.path.dirname(self.folder_data['path']).replace('\\', '/')
            if not path: path = '/'
            # 从父窗口获取当前用户
            current_user = None
            if hasattr(self.parent(), 'username'):
                current_user = self.parent().username
            self.file_system.set_item_hidden(path, self.folder_data['name'], 'dir', new_hidden, current_user)
        self.accept()
        
    def get_file_count(self):
        """获取文件夹中的文件数量"""
        try:
            content = self.file_system.get_directory_content(self.folder_data["path"])
            return len([item for item in content if item['type'] == 'file'])
        except:
            return 0
    
    def get_folder_count(self):
        """获取文件夹中的文件夹数量"""
        try:
            content = self.file_system.get_directory_content(self.folder_data["path"])
            return len([item for item in content if item['type'] == 'dir'])
        except:
            return 0

class FilePropertiesDialog(QDialog):
    """文件属性对话框"""
    def __init__(self, file_data, file_system, parent=None):
        super().__init__(parent)
        self.file_data = file_data
        self.file_system = file_system
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f'文件属性 - {self.file_data["name"]}')
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 文件图标和名称
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(os.path.join(os.path.dirname(__file__), '..', 'data', 'text-x-generic.png')).pixmap(48, 48))
        header_layout.addWidget(icon_label)
        
        name_label = QLabel(self.file_data["name"])
        name_label.setFont(QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 属性信息
        form_layout = QFormLayout()
        
        # 绝对路径
        path_label = QLabel(self.file_data["path"])
        path_label.setWordWrap(True)
        form_layout.addRow('位置:', path_label)
        
        # 文件大小
        size = self.file_data.get("size", 0)
        size_str = self.format_file_size(size)
        form_layout.addRow('大小:', QLabel(size_str))
        
        # 文件类型
        file_type = self.get_file_type()
        form_layout.addRow('类型:', QLabel(file_type))
        
        # 创建时间
        created_time = self.file_data.get("created", "未知")
        form_layout.addRow('创建时间:', QLabel(created_time))
        
        # 修改时间
        modified_time = self.file_data.get("modified", "未知")
        form_layout.addRow('修改时间:', QLabel(modified_time))
        
        layout.addLayout(form_layout)
        
        # 文件属性
        attributes_group = QWidget()
        attributes_layout = QVBoxLayout(attributes_group)
        
        self.is_hidden = QCheckBox('隐藏')
        self.is_hidden.setChecked(self.file_data.get('hidden', False))
        attributes_layout.addWidget(self.is_hidden)
        
        self.is_readonly = QCheckBox('只读')
        self.is_readonly.setChecked(False)
        attributes_layout.addWidget(self.is_readonly)
        
        layout.addWidget(attributes_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.save_properties)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def save_properties(self):
        """保存属性设置"""
        # 保存隐藏状态
        new_hidden = self.is_hidden.isChecked()
        if new_hidden != self.file_data.get('hidden', False):
            path = os.path.dirname(self.file_data['path']).replace('\\', '/')
            if not path: path = '/'
            # 从父窗口获取当前用户
            current_user = None
            if hasattr(self.parent(), 'username'):
                current_user = self.parent().username
            self.file_system.set_item_hidden(path, self.file_data['name'], 'file', new_hidden, current_user)
        self.accept()
        
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} 字节"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def get_file_type(self):
        """获取文件类型"""
        name = self.file_data["name"]
        if '.' in name:
            ext = name.split('.')[-1].lower()
            type_map = {
                'txt': '文本文档',
                'doc': 'Word文档',
                'docx': 'Word文档',
                'pdf': 'PDF文档',
                'jpg': 'JPEG图像',
                'jpeg': 'JPEG图像',
                'png': 'PNG图像',
                'gif': 'GIF图像',
                'mp3': 'MP3音频',
                'mp4': 'MP4视频',
                'avi': 'AVI视频',
                'zip': '压缩文件',
                'rar': '压缩文件',
                'exe': '可执行文件',
                'py': 'Python脚本',
                'js': 'JavaScript文件',
                'html': 'HTML文档',
                'css': 'CSS样式表',
                'json': 'JSON数据文件',
                'xml': 'XML文档'
            }
            return type_map.get(ext, f'{ext.upper()} 文件')
        else:
            return '未知类型' 