# 虚拟文件管理系统 - 核心实现

## 项目概述

这是虚拟文件管理系统的核心实现部分，包含完整的文件系统模拟、用户界面和系统监控功能。

## 快速开始

### 环境准备
```bash
# 安装Python依赖
pip install PyQt5

# 运行程序
python main.py
```

### 默认账号
- **管理员**: admin / admin
- **普通用户**: 需要通过管理员创建

## 核心架构

### 1. 虚拟文件系统 (core/file_system.py)

#### 主要类和方法

**FileSystem类**
```python
class FileSystem:
    def __init__(self):
        # 初始化文件系统，加载JSON数据
        
    def create_file(self, parent_path, filename, content="", current_user=None):
        # 创建文件
        
    def create_directory(self, parent_path, dirname, current_user=None):
        # 创建目录
        
    def delete_item(self, item_path, current_user=None):
        # 删除文件或目录
        
    def copy_item(self, source_path, dest_path, current_user=None):
        # 复制文件或目录
        
    def move_item(self, source_path, dest_path, current_user=None):
        # 移动文件或目录
        
    def get_file_content(self, file_path, current_user=None):
        # 获取文件内容
        
    def save_file_content(self, file_path, content, current_user=None):
        # 保存文件内容
```

#### 数据结构

**文件节点结构**
```json
{
  "name": "文件名",
  "type": "file|dir",
  "path": "/完整路径",
  "created": "创建时间",
  "modified": "修改时间",
  "content": "文件内容",
  "size": 文件大小,
  "hidden": false,
  "children": []
}
```

### 2. 系统监控 (core/system_monitor.py)

#### 监控功能

**性能监控**
- CPU使用率监控
- 内存使用情况
- 系统运行时间统计

**文件系统监控**
- 文件访问日志
- 磁盘使用统计
- 文件缓存管理
- 文件索引维护

**系统健康检查**
- 数据完整性检查
- 性能指标分析
- 异常情况检测

### 3. 用户界面 (ui/)

#### 登录窗口 (login_window.py)
- 用户身份验证
- 新用户注册
- 密码加密存储

#### 用户主窗口 (user_window.py)
- 文件浏览器界面
- 工具栏和菜单
- 右键上下文菜单
- 文件编辑对话框

#### 管理员窗口 (admin_window.py)
- 继承用户窗口功能
- 系统根目录访问
- 用户管理功能
- 系统信息查看

## 数据文件说明

### filesystem.json
虚拟文件系统的核心数据文件，存储完整的目录树结构：
```json
{
  "root": {
    "type": "dir",
    "name": "root",
    "path": "/",
    "children": [
      {
        "name": "home",
        "type": "dir",
        "path": "/home",
        "children": [
          {
            "name": "shared",
            "type": "dir",
            "path": "/home/shared",
            "children": []
          },
          {
            "name": "用户名",
            "type": "dir",
            "path": "/home/用户名",
            "children": []
          }
        ]
      }
    ]
  }
}
```

### users.json
用户账号数据文件：
```json
{
  "admin": {
    "password": "密码哈希值",
    "role": "admin",
    "created": "创建时间"
  },
  "用户名": {
    "password": "密码哈希值",
    "role": "user",
    "created": "创建时间"
  }
}
```

### config.ini
系统配置文件：
```ini
[System]
default_user = admin
max_file_size = 1048576
cache_size = 100

[UI]
theme = default
language = zh_CN
show_hidden_files = false

[Security]
password_min_length = 6
max_login_attempts = 3
```

## 权限系统

### 权限模型
- **管理员权限**: 访问所有目录，管理用户
- **普通用户权限**: 访问个人目录和共享目录

### 权限检查
```python
def check_access_permission(self, user, path):
    # 检查用户是否有权限访问指定路径
    if user == "admin":
        return True
    elif path.startswith(f"/home/{user}"):
        return True
    elif path.startswith("/home/shared"):
        return True
    else:
        return False
```

## 文件操作流程

### 1. 创建文件
```python
# 1. 检查权限
if not file_system.check_access_permission(user, parent_path):
    return False

# 2. 验证路径
if not file_system._get_node_by_path(parent_path):
    return False

# 3. 创建文件节点
file_node = {
    "name": filename,
    "type": "file",
    "path": f"{parent_path}/{filename}",
    "content": content,
    "size": len(content),
    "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "hidden": False
}

# 4. 添加到父节点
parent_node["children"].append(file_node)

# 5. 保存到JSON
file_system.save_file_system()
```

### 2. 文件编辑
```python
# 1. 获取文件内容
content = file_system.get_file_content(file_path, user)

# 2. 显示编辑对话框
dialog = FileEditDialog(content, file_path, user)

# 3. 保存修改
if dialog.exec_() == QDialog.Accepted:
    new_content = dialog.get_content()
    file_system.save_file_content(file_path, new_content, user)
```

## 缓存机制

### 文件缓存
- 最近访问的文件内容缓存
- 减少JSON文件读取次数
- 提高文件访问速度

### 索引缓存
- 文件路径索引
- 搜索优化
- 快速定位文件

## 错误处理

### 常见错误类型
1. **权限错误**: 用户无权限访问指定路径
2. **路径错误**: 文件或目录不存在
3. **数据错误**: JSON文件格式错误
4. **系统错误**: 内存不足、磁盘空间不足

### 错误处理策略
```python
try:
    # 执行文件操作
    result = file_system.create_file(path, filename, content, user)
except PermissionError:
    QMessageBox.warning(None, "权限错误", "您没有权限执行此操作")
except FileNotFoundError:
    QMessageBox.warning(None, "路径错误", "指定的路径不存在")
except Exception as e:
    QMessageBox.critical(None, "系统错误", f"操作失败: {str(e)}")
```

## 性能优化

### 1. 文件缓存
- 缓存最近访问的文件内容
- 减少重复的JSON读取操作

### 2. 索引优化
- 维护文件路径索引
- 加速文件搜索和定位

### 3. 异步操作
- 大文件操作异步处理
- 避免界面卡顿

### 4. 内存管理
- 及时释放不需要的缓存
- 控制缓存大小

## 开发指南

### 添加新功能

1. **在core模块中添加核心逻辑**
2. **在ui模块中添加界面组件**
3. **更新权限检查逻辑**
4. **添加错误处理**
5. **更新文档**

### 代码规范

1. **命名规范**
   - 类名使用PascalCase
   - 方法名使用snake_case
   - 常量使用UPPER_CASE

2. **注释规范**
   - 类和方法必须有文档字符串
   - 复杂逻辑需要行内注释

3. **错误处理**
   - 所有可能出错的地方都要有异常处理
   - 提供有意义的错误信息

### 测试建议

1. **单元测试**
   - 测试核心文件系统功能
   - 测试权限检查逻辑

2. **集成测试**
   - 测试完整的用户操作流程
   - 测试界面交互

3. **性能测试**
   - 测试大量文件操作
   - 测试内存使用情况

## 部署说明

### 开发环境
```bash
# 克隆项目
git clone <项目地址>

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### 生产环境
```bash
# 编译为可执行文件
pyinstaller --onefile --windowed main.py

# 部署文件
dist/main.exe
```

## 维护说明

### 数据备份
- 定期备份filesystem.json
- 定期备份users.json
- 定期备份config.ini

### 日志管理
- 检查system_log.json
- 清理过期的日志数据
- 监控系统性能指标

### 更新维护
- 定期更新依赖包
- 修复已知问题
- 优化性能瓶颈

## 常见问题

### Q: 文件保存后内容丢失
A: 检查文件系统权限，确认JSON文件可写

### Q: 登录失败
A: 检查users.json文件格式，确认密码哈希正确

### Q: 程序启动缓慢
A: 检查filesystem.json文件大小，清理不必要的数据

### Q: 界面显示异常
A: 检查PyQt5版本兼容性，确认图标文件存在

---

**开发团队**: 操作系统课程设计小组  
**版本**: v1.4  
**最后更新**: 2025年1月 