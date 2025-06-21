# OS课程设计——虚拟文件管理系统

## 项目简介

这是一个基于PyQt5开发的虚拟文件管理系统，模拟了操作系统的文件管理功能。系统采用虚拟文件系统（VFS）架构，所有文件数据存储在JSON格式的配置文件中，支持多用户权限管理、文件操作、系统监控等功能。

## 功能特性

### 核心功能
- **多用户权限管理**：支持管理员和普通用户，不同权限级别
- **虚拟文件系统**：基于JSON的虚拟文件存储，支持目录树结构
- **文件操作**：创建、删除、重命名、复制、剪切、粘贴文件/文件夹
- **文件编辑**：内置文本编辑器，支持文件内容编辑和保存
- **文件属性**：查看和修改文件属性，支持隐藏文件功能
- **搜索功能**：递归搜索文件和文件夹
- **文件排序**：按名称、大小、类型、修改时间排序
- **文件预览**：支持文本文件预览

### 高级功能
- **系统监控**：实时监控系统性能、磁盘使用、访问日志
- **文件缓存**：智能文件缓存机制，提高访问速度
- **文件索引**：自动建立文件索引，优化搜索性能
- **访问日志**：记录所有文件操作日志
- **系统健康检查**：监控系统运行状态

### 用户界面
- **现代化UI**：基于PyQt5的图形用户界面
- **树形目录**：左侧树形目录导航
- **列表视图**：右侧文件列表显示
- **工具栏**：常用操作快捷按钮
- **右键菜单**：上下文菜单操作
- **状态栏**：显示当前状态和文件统计



## 1. 开发环境要求

### 1.1 系统要求
- **操作系统**：Windows 10/11 (推荐) 或 Linux/macOS
- **Python版本**：Python 3.7 或更高版本
- **内存**：建议 4GB 以上
- **磁盘空间**：至少 1GB 可用空间

### 1.2 必需软件
- **Anaconda/Miniconda**：用于环境管理
- **Python IDE**：推荐 PyCharm、VS Code 或 IDLE

---

## 2. 环境配置详细步骤

### 2.1 安装 Anaconda/Miniconda（建议选择miniconda3）

#### Windows 用户：
1. 访问 [Anaconda官网](https://www.anaconda.com/) 或 [Miniconda官网](https://docs.conda.io/en/latest/miniconda.html)
2. 下载适合 Windows 的安装包（推荐 64-bit）
3. 运行安装程序，建议选择"Install for All Users"
4. 安装完成后，打开 Anaconda Prompt 或命令提示符

#### Linux/macOS 用户：
```bash
# 下载并安装 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### 2.2 验证安装
```bash
# 检查 conda 版本
conda --version

# 检查 Python 版本
python --version
```

### 2.3 创建项目环境

#### 方法一：使用环境配置文件（推荐）
```bash
# 进入可执行程序目录
cd 可执行程序

# 创建 conda 环境
conda env create -f environment.yaml

# 激活环境
conda activate OS
```

#### 方法二：手动创建环境
```bash
# 创建新的 conda 环境
conda create -n OS python=3.8

# 激活环境
conda activate OS

# 安装必要的包
pip install PyQt5==5.15.0
pip install psutil==5.8.0
```

### 2.4 验证环境配置
```bash
# 检查已安装的包
pip list

# 测试 PyQt5 导入
python -c "import PyQt5; print('PyQt5 安装成功')"
```

---

## 3. 运行程序

### 3.1 进入项目目录
```bash
# 确保在激活的环境中
conda activate OS

# 进入源程序目录
cd ../源程序/files
```

### 3.2 启动主程序
```bash
# 运行主程序
python main.py
```

### 3.3 程序启动验证
- 程序启动后应显示登录窗口
- 默认管理员账号：admin / admin123
- 可以正常登录并进入主界面
