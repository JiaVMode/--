"""
系统监控对话框
显示磁盘使用统计、性能监控和访问日志等信息
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QTabWidget, QWidget,
                             QListWidget, QListWidgetItem, QProgressBar,
                             QTableWidget, QTableWidgetItem, QGroupBox,
                             QGridLayout, QSplitter, QFrame, QHeaderView)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor

class SystemMonitorDialog(QDialog):
    """系统监控对话框"""
    
    def __init__(self, file_system, system_monitor, parent=None):
        super().__init__(parent)
        self.file_system = file_system
        self.system_monitor = system_monitor
        
        # 设置为非模态窗口
        self.setModal(False)
        
        # 设置窗口标志，允许窗口置顶
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.init_ui()
        self.setup_timers()
        self.refresh_data()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("系统监控")
        self.setGeometry(400, 300, 1000, 700)
        
        # 设置图标
        icon_path = os.path.join(os.path.dirname(__file__), "..", "data", "applications-system.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        layout = QVBoxLayout()
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 性能监控标签页
        performance_tab = self.create_performance_tab()
        tab_widget.addTab(performance_tab, "性能监控")
        
        # 磁盘使用标签页
        disk_tab = self.create_disk_tab()
        tab_widget.addTab(disk_tab, "磁盘使用")
        
        # 访问日志标签页
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "访问日志")
        
        # 系统健康标签页
        health_tab = self.create_health_tab()
        tab_widget.addTab(health_tab, "系统健康")
        
        layout.addWidget(tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_data)
        cleanup_button = QPushButton("清理日志")
        cleanup_button.clicked.connect(self.cleanup_logs)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(cleanup_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_performance_tab(self):
        """创建性能监控标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # CPU使用率
        cpu_group = QGroupBox("CPU使用率")
        cpu_layout = QVBoxLayout()
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_label = QLabel("0%")
        cpu_layout.addWidget(self.cpu_progress)
        cpu_layout.addWidget(self.cpu_label)
        cpu_group.setLayout(cpu_layout)
        layout.addWidget(cpu_group)
        
        # 内存使用率
        memory_group = QGroupBox("内存使用率")
        memory_layout = QVBoxLayout()
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_label = QLabel("0%")
        memory_layout.addWidget(self.memory_progress)
        memory_layout.addWidget(self.memory_label)
        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)
        
        # 磁盘使用率
        disk_group = QGroupBox("磁盘使用率")
        disk_layout = QVBoxLayout()
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        self.disk_label = QLabel("0%")
        disk_layout.addWidget(self.disk_progress)
        disk_layout.addWidget(self.disk_label)
        disk_group.setLayout(disk_layout)
        layout.addWidget(disk_group)
        
        # 缓存信息
        cache_group = QGroupBox("缓存信息")
        cache_layout = QGridLayout()
        cache_layout.addWidget(QLabel("缓存命中率:"), 0, 0)
        self.cache_hit_label = QLabel("0%")
        cache_layout.addWidget(self.cache_hit_label, 0, 1)
        cache_layout.addWidget(QLabel("缓存大小:"), 1, 0)
        self.cache_size_label = QLabel("0 MB")
        cache_layout.addWidget(self.cache_size_label, 1, 1)
        cache_layout.addWidget(QLabel("缓存条目:"), 2, 0)
        self.cache_entries_label = QLabel("0")
        cache_layout.addWidget(self.cache_entries_label, 2, 1)
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_disk_tab(self):
        """创建磁盘使用标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 总体统计
        overall_group = QGroupBox("总体统计")
        overall_layout = QGridLayout()
        overall_layout.addWidget(QLabel("总文件数:"), 0, 0)
        self.total_files_label = QLabel("0")
        overall_layout.addWidget(self.total_files_label, 0, 1)
        overall_layout.addWidget(QLabel("总目录数:"), 1, 0)
        self.total_dirs_label = QLabel("0")
        overall_layout.addWidget(self.total_dirs_label, 1, 1)
        overall_layout.addWidget(QLabel("总大小:"), 2, 0)
        self.total_size_label = QLabel("0 MB")
        overall_layout.addWidget(self.total_size_label, 2, 1)
        overall_group.setLayout(overall_layout)
        layout.addWidget(overall_group)
        
        # 文件类型统计
        file_type_group = QGroupBox("文件类型统计")
        file_type_layout = QVBoxLayout()
        self.file_type_table = QTableWidget()
        self.file_type_table.setColumnCount(2)
        self.file_type_table.setHorizontalHeaderLabels(["文件类型", "数量"])
        self.file_type_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        file_type_layout.addWidget(self.file_type_table)
        file_type_group.setLayout(file_type_layout)
        layout.addWidget(file_type_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_log_tab(self):
        """创建访问日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 日志摘要
        summary_group = QGroupBox("日志摘要")
        summary_layout = QGridLayout()
        summary_layout.addWidget(QLabel("总操作数:"), 0, 0)
        self.total_ops_label = QLabel("0")
        summary_layout.addWidget(self.total_ops_label, 0, 1)
        summary_layout.addWidget(QLabel("时间范围:"), 1, 0)
        self.time_range_label = QLabel("最近24小时")
        summary_layout.addWidget(self.time_range_label, 1, 1)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # 操作类型统计
        ops_group = QGroupBox("操作类型统计")
        ops_layout = QVBoxLayout()
        self.ops_table = QTableWidget()
        self.ops_table.setColumnCount(2)
        self.ops_table.setHorizontalHeaderLabels(["操作类型", "次数"])
        self.ops_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        ops_layout.addWidget(self.ops_table)
        ops_group.setLayout(ops_layout)
        layout.addWidget(ops_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_health_tab(self):
        """创建系统健康标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 健康评分
        health_group = QGroupBox("系统健康评分")
        health_layout = QVBoxLayout()
        self.health_progress = QProgressBar()
        self.health_progress.setRange(0, 100)
        self.health_label = QLabel("健康评分: 0/100")
        health_layout.addWidget(self.health_progress)
        health_layout.addWidget(self.health_label)
        health_group.setLayout(health_layout)
        layout.addWidget(health_group)
        
        # 优化建议
        recommendations_group = QGroupBox("优化建议")
        recommendations_layout = QVBoxLayout()
        self.recommendations_list = QListWidget()
        recommendations_layout.addWidget(self.recommendations_list)
        recommendations_group.setLayout(recommendations_layout)
        layout.addWidget(recommendations_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def setup_timers(self):
        """设置定时器"""
        # 每5秒更新性能数据
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance)
        self.performance_timer.start(5000)
    
    def refresh_data(self):
        """刷新所有数据"""
        self.update_performance()
        self.update_disk_usage()
        self.update_access_log()
        self.update_health_report()
    
    def update_performance(self):
        """更新性能数据"""
        try:
            performance = self.system_monitor.get_performance_stats()
            
            # CPU使用率
            cpu_usage = performance['cpu_usage']
            self.cpu_progress.setValue(int(cpu_usage))
            self.cpu_label.setText(f"{cpu_usage:.1f}%")
            
            # 内存使用率
            memory_usage = performance['memory_usage']
            self.memory_progress.setValue(int(memory_usage))
            self.memory_label.setText(f"{memory_usage:.1f}%")
            
            # 磁盘使用率
            disk_usage = performance['disk_usage']
            self.disk_progress.setValue(int(disk_usage))
            self.disk_label.setText(f"{disk_usage:.1f}%")
            
            # 缓存信息
            cache_hit_rate = performance['cache_hit_rate']
            self.cache_hit_label.setText(f"{cache_hit_rate:.1f}%")
            
            cache_size_mb = performance['cache_size'] / (1024 * 1024)
            self.cache_size_label.setText(f"{cache_size_mb:.1f} MB")
            
            self.cache_entries_label.setText(str(performance['cache_entries']))
            
        except Exception as e:
            print(f"更新性能数据失败: {e}")
    
    def update_disk_usage(self):
        """更新磁盘使用数据"""
        try:
            disk_stats = self.system_monitor.get_disk_usage_stats()
            
            # 总体统计
            self.total_files_label.setText(str(disk_stats['total_files']))
            self.total_dirs_label.setText(str(disk_stats['total_dirs']))
            
            total_size_mb = disk_stats['total_size'] / (1024 * 1024)
            self.total_size_label.setText(f"{total_size_mb:.1f} MB")
            
            # 文件类型统计
            file_types = disk_stats['file_type_stats']
            self.file_type_table.setRowCount(len(file_types))
            for i, (ext, count) in enumerate(sorted(file_types.items(), key=lambda x: x[1], reverse=True)):
                self.file_type_table.setItem(i, 0, QTableWidgetItem(f".{ext}"))
                self.file_type_table.setItem(i, 1, QTableWidgetItem(str(count)))
            
        except Exception as e:
            print(f"更新磁盘使用数据失败: {e}")
    
    def update_access_log(self):
        """更新访问日志数据"""
        try:
            log_summary = self.system_monitor.get_access_log_summary()
            
            # 日志摘要
            self.total_ops_label.setText(str(log_summary['total_operations']))
            self.time_range_label.setText(log_summary['time_range'])
            
            # 操作类型统计
            operations = log_summary['operation_stats']
            self.ops_table.setRowCount(len(operations))
            for i, (op, count) in enumerate(sorted(operations.items(), key=lambda x: x[1], reverse=True)):
                self.ops_table.setItem(i, 0, QTableWidgetItem(op))
                self.ops_table.setItem(i, 1, QTableWidgetItem(str(count)))
            
        except Exception as e:
            print(f"更新访问日志数据失败: {e}")
    
    def update_health_report(self):
        """更新系统健康报告"""
        try:
            health_report = self.system_monitor.get_system_health_report()
            
            # 健康评分
            health_score = health_report['health_score']
            self.health_progress.setValue(int(health_score))
            self.health_label.setText(f"健康评分: {health_score:.0f}/100")
            
            # 优化建议
            recommendations = health_report['recommendations']
            self.recommendations_list.clear()
            for recommendation in recommendations:
                self.recommendations_list.addItem(recommendation)
            
        except Exception as e:
            print(f"更新系统健康报告失败: {e}")
    
    def cleanup_logs(self):
        """清理日志"""
        try:
            self.system_monitor.cleanup_old_logs(7)  # 清理7天前的日志
            self.refresh_data()
        except Exception as e:
            print(f"清理日志失败: {e}")
    
    def closeEvent(self, event):
        """关闭事件"""
        self.performance_timer.stop()
        event.accept() 