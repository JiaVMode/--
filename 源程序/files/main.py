"""
虚拟文件管理器 - 主程序入口
操作系统课程设计项目

作者: 李嘉
版本: 1.0
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon

def get_data_dir():
    """获取数据目录路径"""
    # 如果是exe文件运行，使用exe文件所在目录
    if getattr(sys, 'frozen', False):
        # 运行在PyInstaller打包的环境中
        base_path = sys._MEIPASS
        data_dir = os.path.join(base_path, 'data')
    else:
        # 运行在开发环境中
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_path, 'data')
    
    return data_dir

def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("虚拟文件管理器")
        app.setApplicationVersion("1.0")
        
        # 获取数据目录
        data_dir = get_data_dir()
        
        # 设置应用程序图标
        icon_path = os.path.join(data_dir, 'applications-system.png')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # 初始化文件系统
        from core.file_system import FileSystem
        file_system = FileSystem(data_dir)
        
        # 创建登录窗口
        from ui.login_window import LoginWindow
        login_window = LoginWindow(file_system)
        login_window.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        # 显示错误信息
        error_msg = f"程序启动失败：{str(e)}"
        print(error_msg)
        
        # 如果有GUI环境，显示错误对话框
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "错误", error_msg)
        except:
            pass
        
        input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main() 