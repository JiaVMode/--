##########################################
#            普通用户窗口
#             作者：李嘉
#           学号：3123009043
#          班级：23人工智能1班
#         指导教师：苏畅、李剑锋
###########################################
"""
普通用户主窗口 - 基于JSON文件系统
"""

import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QMessageBox,
                             QToolBar, QAction, QStatusBar, QMenuBar, QMenu,
                             QListWidget, QListWidgetItem, QSplitter, QTreeWidget,
                             QTreeWidgetItem, QLineEdit, QInputDialog, QDialog,
                             QTextEdit, QDialogButtonBox, QFormLayout,
                             QSizePolicy, QCheckBox, QFileDialog, QSpinBox,
                             QGroupBox, QTabWidget)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont

from core.file_system import FileSystem
from .system_monitor_dialog import SystemMonitorDialog

class UserWindow(QMainWindow):
    def __init__(self, username, file_system):
        super().__init__()
        self.username = username
        self.file_system = file_system
        self.home_path = f"/home/{username}"
        self.current_path = self.home_path
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
        self.setWindowTitle(f"文件管理器 - 用户 ({self.username})")
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
        self.address_edit = QLineEdit(self.current_path)
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
        
        splitter.setSizes([250, 850])
        main_layout.addWidget(splitter)
        
        self.setStatusBar(QStatusBar())

        self.refresh_view()

    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        file_menu.addAction('新建文件夹', self.create_new_folder)
        file_menu.addAction('新建文件', self.create_new_file)
        file_menu.addSeparator()
        file_menu.addAction('退出', self.close)

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
        help_menu.addAction("关于", self.show_about)

    def create_toolbar(self):
        toolbar = self.addToolBar('主工具栏')
        toolbar.addAction(QIcon(os.path.join(self.file_system.data_dir, 'go-up.png')), "上一级", self.go_up)
        toolbar.addSeparator()
        toolbar.addAction(QIcon(os.path.join(self.file_system.data_dir, 'folder-new.png')), "新建文件夹", self.create_new_folder)
        toolbar.addAction(QIcon(os.path.join(self.file_system.data_dir, 'document-new.png')), "新建文件", self.create_new_file)
        toolbar.addSeparator()
        toolbar.addAction(QIcon(os.path.join(self.file_system.data_dir, 'edit-copy.png')), "复制", self.toolbar_copy)
        toolbar.addAction(QIcon(os.path.join(self.file_system.data_dir, 'edit-cut.png')), "剪切", self.toolbar_cut)
        toolbar.addAction(QIcon(os.path.join(self.file_system.data_dir, 'edit-paste.png')), "粘贴", self.toolbar_paste)
        toolbar.addSeparator()
        toolbar.addAction(QIcon(os.path.join(self.file_system.data_dir, 'edit-delete.png')), "删除", self.toolbar_delete)
        toolbar.addAction(QIcon(os.path.join(self.file_system.data_dir, 'edit-rename.png')), "重命名", self.toolbar_rename)
        toolbar.addSeparator()
        toolbar.addAction(QIcon(os.path.join(self.file_system.data_dir, 'view-refresh.png')), "刷新", self.refresh_view)

    def load_tree_structure(self):
        self.tree_widget.clear()
        
        # 获取/home目录下的所有子目录
        home_node = self.file_system._get_node_by_path("/home")
        if not home_node:
            return
            
        # 为每个子目录创建树形项
        for child in home_node.get('children', []):
            if isinstance(child, dict) and child.get('type') == 'dir':
                # 检查用户是否有权限访问此目录
                if self.file_system.check_access_permission(self.username, child.get('path', '')):
                    # 创建树形项
                    if child.get('name') == self.username:
                        # 当前用户的目录，显示为用户名
                        tree_item = QTreeWidgetItem(self.tree_widget, [self.username])
                    else:
                        # 其他目录（如shared或其他用户目录）
                        tree_item = QTreeWidgetItem(self.tree_widget, [child.get('name')])
                    
                    tree_item.setData(0, Qt.UserRole, child)
                    tree_item.setIcon(0, self.icon_provider['dir'])
                    
                    # 递归添加子目录
                    self._add_tree_items_recursive(tree_item, child.get('children', []))
                    self.tree_widget.expandItem(tree_item)

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
        
        if not self.file_system.check_access_permission(self.username, path):
            QMessageBox.warning(self, "权限错误", "您没有权限访问此目录。")
            self.current_path = self.home_path
            self.address_edit.setText(self.current_path)
            content = self.file_system.get_directory_content(self.current_path, self.username, self.show_hidden_files)
        else:
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
            
            # 如果文件被隐藏，使用不同的图标或样式
            if item_data.get('hidden', False):
                list_item.setIcon(self.icon_provider.get(item_data['type'], self.icon_provider['unknown']))
                # 可以设置不同的字体或颜色来表示隐藏文件
                font = list_item.font()
                font.setItalic(True)
                list_item.setFont(font)
            else:
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
        else:
            self.open_file(item_data)

    def navigate_from_address_bar(self):
        path = self.address_edit.text()
        self.load_directory(path)

    def go_up(self):
        parent_path = os.path.dirname(self.current_path).replace('\\', '/')
        if not parent_path: parent_path = '/'
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
        self.file_edit_dialog = FileEditDialog(item_data, content, self.file_system, self.username, self)
        self.file_edit_dialog.show()

    # --- Context Menu and Actions ---
    def show_context_menu(self, position):
        menu = QMenu()
        selected_items = self.list_widget.selectedItems()

        if selected_items:
            menu.addAction("打开", self.context_open)
            menu.addAction("预览", self.context_preview)
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

    def context_preview(self):
        """预览文件"""
        selected_data = self.get_selected_items_data()
        if not selected_data or len(selected_data) != 1:
            QMessageBox.information(self, "预览", "请选择一个文件进行预览")
            return
            
        item_data = selected_data[0]
        if item_data['type'] != 'file':
            QMessageBox.information(self, "预览", "只能预览文件")
            return
            
        # 检查文件类型是否支持预览
        name = item_data['name'].lower()
        if not any(ext in name for ext in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.log']):
            QMessageBox.information(self, "预览", "此文件类型不支持预览")
            return
            
        # 获取文件内容
        content = self.file_system.get_file_content(item_data['path'], self.username)
        if content is None:
            QMessageBox.warning(self, "预览", "无法读取文件内容")
            return
            
        # 显示预览对话框
        self.preview_dialog = FilePreviewDialog(item_data, content, self)
        self.preview_dialog.show()

    def context_rename(self):
        selected_data = self.get_selected_items_data()
        if not selected_data: return
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

    def context_show_item(self):
        selected_data = self.get_selected_items_data()
        if not selected_data: return
        for item_data in selected_data:
            self.file_system.unhide_item(self.current_path, item_data['name'], item_data['type'], self.username)
        self.refresh_view()

    def context_hide_item(self):
        selected_data = self.get_selected_items_data()
        if not selected_data: return
        for item_data in selected_data:
            self.file_system.hide_item(self.current_path, item_data['name'], item_data['type'], self.username)
        self.refresh_view()

    def toggle_show_hidden(self):
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
        
    def show_system_info(self):
        """显示系统信息"""
        import platform
        info = f"操作系统: {platform.system()} {platform.release()}\n"
        info += f"Python版本: {platform.python_version()}\n"
        info += f"PyQt5版本: {self.get_pyqt_version()}\n"
        info += f"当前用户: {self.username}\n"
        info += f"当前路径: {self.current_path}\n"
        info += f"用户主目录: {self.home_path}"
        
        QMessageBox.information(self, "系统信息", info)
        
    def get_pyqt_version(self):
        """获取PyQt5版本"""
        try:
            from PyQt5.QtCore import QT_VERSION_STR
            return QT_VERSION_STR
        except:
            return "未知"

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
            
            # 如果文件被隐藏，使用不同的样式
            if item_data.get('hidden', False):
                font = list_item.font()
                font.setItalic(True)
                list_item.setFont(font)
            
            self.list_widget.addItem(list_item)
        
        order_text = "降序" if sort_order == 'desc' else "升序"
        self.statusBar().showMessage(f"已按{sort_key}{order_text}排序，共 {len(sorted_content)} 项")

    def format_file_size(self, size_bytes):
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
            # 检查用户是否有权限访问该路径
            if not self.has_permission_to_access(path):
                QMessageBox.warning(self, '权限错误', f'您没有权限访问路径: {path}')
                # 重置为用户主目录
                user_home = f"/home/{self.username}"
                self.address_edit.setText(user_home)
                self.refresh_file_list(user_home)
                return
            self.refresh_file_list(path)
            
    def has_permission_to_access(self, path):
        """检查用户是否有权限访问指定路径"""
        # 检查路径是否为空或无效
        if not path or not isinstance(path, str):
            return False
            
        # 用户总是可以访问自己的主目录
        user_home = f"/home/{self.username}"
        if path == user_home or path.startswith(user_home + '/'):
            return True
        
        # 用户可以访问共享目录
        if path == "/home/shared" or path.startswith("/home/shared/"):
            return True
        
        # 其他路径需要检查权限
        try:
            # 尝试获取目录内容来检查权限
            content = self.file_system.get_directory_content(path, self.username, False)
            return content is not None
        except:
            return False


# --- Helper Dialogs ---

class FileEditDialog(QDialog):
    def __init__(self, file_info, content, file_system, username, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.file_system = file_system
        self.username = username
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
        
        # 添加调试信息
        print(f"保存文件调试信息:")
        print(f"  文件路径: {self.file_info['path']}")
        print(f"  目录路径: {dir_path}")
        print(f"  文件名: {file_name}")
        print(f"  用户名: {self.username}")
        print(f"  内容长度: {len(new_content)}")
        
        success = self.file_system.write_file(dir_path, file_name, new_content, self.username)
        
        # 添加调试信息
        print(f"  保存结果: {success}")
        
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

class FilePropertiesDialog(QDialog):
    def __init__(self, file_data, file_system, parent=None):
        super().__init__(parent)
        self.file_data = file_data
        self.file_system = file_system
        
        # 设置为非模态窗口
        self.setModal(False)
        
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"属性 - {self.file_data['name']}")
        layout = QVBoxLayout(self)
        
        # 基本信息
        form_layout = QFormLayout()
        form_layout.addRow("名称:", QLabel(self.file_data['name']))
        form_layout.addRow("类型:", QLabel("文件"))
        form_layout.addRow("位置:", QLabel(self.file_data['path']))
        size_str = f"{self.file_data.get('size', 0)} 字节"
        form_layout.addRow("大小:", QLabel(size_str))
        form_layout.addRow("创建时间:", QLabel(self.file_data.get('created', '')))
        form_layout.addRow("修改时间:", QLabel(self.file_data.get('modified', '')))
        layout.addLayout(form_layout)
        
        # 隐藏选项
        self.hidden_checkbox = QCheckBox("隐藏")
        self.hidden_checkbox.setChecked(self.file_data.get('hidden', False))
        layout.addWidget(self.hidden_checkbox)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_properties)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def save_properties(self):
        # 保存隐藏状态
        new_hidden = self.hidden_checkbox.isChecked()
        if new_hidden != self.file_data.get('hidden', False):
            path = os.path.dirname(self.file_data['path']).replace('\\', '/')
            if not path: path = '/'
            # 从父窗口获取当前用户
            current_user = None
            if hasattr(self.parent(), 'username'):
                current_user = self.parent().username
            self.file_system.set_item_hidden(path, self.file_data['name'], 'file', new_hidden, current_user)
        self.accept()

class FolderPropertiesDialog(QDialog):
    def __init__(self, folder_data, file_system, parent=None):
        super().__init__(parent)
        self.folder_data = folder_data
        self.file_system = file_system
        
        # 设置为非模态窗口
        self.setModal(False)
        
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"属性 - {self.folder_data['name']}")
        layout = QVBoxLayout(self)
        
        # 基本信息
        form_layout = QFormLayout()
        form_layout.addRow("名称:", QLabel(self.folder_data['name']))
        form_layout.addRow("类型:", QLabel("文件夹"))
        form_layout.addRow("位置:", QLabel(self.folder_data['path']))
        
        folder_count, file_count = self.get_contents_count(self.folder_data)
        form_layout.addRow("包含:", QLabel(f"{file_count} 个文件, {folder_count} 个文件夹"))
        
        form_layout.addRow("创建时间:", QLabel(self.folder_data.get('created', '')))
        form_layout.addRow("修改时间:", QLabel(self.folder_data.get('modified', '')))
        layout.addLayout(form_layout)
        
        # 隐藏选项
        self.hidden_checkbox = QCheckBox("隐藏")
        self.hidden_checkbox.setChecked(self.folder_data.get('hidden', False))
        layout.addWidget(self.hidden_checkbox)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_properties)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def save_properties(self):
        # 保存隐藏状态
        new_hidden = self.hidden_checkbox.isChecked()
        if new_hidden != self.folder_data.get('hidden', False):
            path = os.path.dirname(self.folder_data['path']).replace('\\', '/')
            if not path: path = '/'
            # 从父窗口获取当前用户
            current_user = None
            if hasattr(self.parent(), 'username'):
                current_user = self.parent().username
            self.file_system.set_item_hidden(path, self.folder_data['name'], 'dir', new_hidden, current_user)
        self.accept()

    def get_contents_count(self, node):
        f_count, d_count = 0, 0
        for child in node.get('children', []):
            if child['type'] == 'dir':
                d_count += 1
                sub_d, sub_f = self.get_contents_count(child)
                d_count += sub_d
                f_count += sub_f
            else:
                f_count += 1
        return d_count, f_count


class FilePreviewDialog(QDialog):
    """文件预览对话框"""
    def __init__(self, file_info, content, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.content = content
        
        # 设置为非模态窗口
        self.setModal(False)
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"文件预览 - {self.file_info['name']}")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 文件信息
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"文件：{self.file_info['name']}"))
        info_layout.addWidget(QLabel(f"大小：{self.file_info.get('size', 0)} 字节"))
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 内容显示区域
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.content)
        self.text_edit.setReadOnly(True)  # 只读模式
        layout.addWidget(self.text_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("打开编辑")
        open_btn.clicked.connect(self.open_for_edit)
        button_layout.addWidget(open_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def open_for_edit(self):
        """打开文件进行编辑"""
        self.accept()
        # 触发父窗口的打开文件功能
        if hasattr(self.parent(), 'open_file'):
            self.parent().open_file(self.file_info) 