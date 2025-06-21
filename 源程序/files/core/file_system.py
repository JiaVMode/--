##########################################
#            文件管理功能模块
#             作者：李嘉
#           学号：3123009043
#          班级：23人工智能1班
#         指导教师：苏畅、李剑锋
###########################################
"""
基于JSON的文件系统管理器
"""

import json
import os
import datetime
import hashlib
import shutil
import copy
from typing import Dict, List, Optional, Tuple

# 导入系统监控器
from .system_monitor import SystemMonitor

class FileSystem:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.fs_file = os.path.join(data_dir, 'filesystem.json')
        self.users_file = os.path.join(data_dir, 'users.json')
        self.file_system = self.load_file_system()
        
        # 剪贴板
        self.clipboard = {
            'type': None,  # 'copy' 或 'cut'
            'items': [],   # 要操作的项目列表
            'source_path': None  # 源路径
        }
        
        # 初始化系统监控器
        self.system_monitor = SystemMonitor(self)

    def _get_node_by_path(self, path: str) -> Optional[Dict]:
        """通过路径获取节点，只沿着目录走"""
        if path == '/':
            return self.file_system.get('root')

        parts = [p for p in path.split('/') if p]
        current_node = self.file_system.get('root')
        if not current_node:
            return None

        for part in parts:
            found = False
            # 确保children是列表且只包含字典类型
            children = current_node.get("children", [])
            if not isinstance(children, list):
                return None
                
            for child in children:
                if isinstance(child, dict) and child.get("name") == part and child.get("type") == "dir":
                    current_node = child
                    found = True
                    break
            if not found:
                return None
        return current_node

    def _find_child_in_node(self, parent_node: Dict, child_name: str, child_type: str = None) -> Optional[Tuple[int, Dict]]:
        """在父节点中查找子项，返回其索引和数据"""
        if not parent_node or "children" not in parent_node:
            return None
            
        children = parent_node["children"]
        if not isinstance(children, list):
            return None
            
        for i, child in enumerate(children):
            if isinstance(child, dict) and child.get("name") == child_name:
                if child_type is None or child.get("type") == child_type:
                    return i, child
        return None

    def load_file_system(self) -> Dict:
        """加载文件系统数据"""
        if not os.path.exists(self.fs_file):
            fs_data = {
                "root": {
                    "name": "root", "type": "dir", "path": "/",
                    "created": self.get_current_time(), "modified": self.get_current_time(),
                    "children": []
                }
            }
        else:
            try:
                with open(self.fs_file, 'r', encoding='utf-8') as f:
                    fs_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"加载文件系统失败: {e}, 将创建新的文件系统。")
                fs_data = {
                    "root": {
                        "name": "root", "type": "dir", "path": "/",
                        "created": self.get_current_time(), "modified": self.get_current_time(),
                        "children": []
                    }
                }

        # 确保 /home 和 /home/shared 目录存在
        self._ensure_required_directories(fs_data)
        
        self.save_file_system(fs_data)
        return fs_data

    def _ensure_required_directories(self, fs_data):
        """确保必要的目录存在"""
        try:
            root_node = fs_data.get('root')
            if not root_node:
                return
            # 强制children为list
            if not isinstance(root_node.get('children'), list):
                root_node['children'] = []
            
            # 确保home_node为dict且children为list
            # 查找home_node
            home_node = None
            for child in root_node['children']:
                if not isinstance(child, dict):
                    continue
                if child.get('name') == 'home' and child.get('type') == 'dir':
                    home_node = child
                    break
            if not home_node:
                home_node = {
                    "name": "home", "type": "dir", "path": "/home",
                    "created": self.get_current_time(), "modified": self.get_current_time(),
                    "children": []
                }
                root_node['children'].append(home_node)
            # 强制children为list
            if not isinstance(home_node.get('children'), list):
                home_node['children'] = []
            # 清理home_node['children']，只保留dict类型，并删除users文件夹
            home_node['children'] = [c for c in home_node['children'] if isinstance(c, dict) and c.get('name') != 'users']
            
            # 检查并创建 /home/shared 目录
            shared_exists = False
            for child in home_node['children']:
                if not isinstance(child, dict):
                    continue
                if child.get('name') == 'shared' and child.get('type') == 'dir':
                    shared_exists = True
                    break
            if not shared_exists:
                shared_node = {
                    "name": "shared", "type": "dir", "path": "/home/shared",
                    "created": self.get_current_time(), "modified": self.get_current_time(),
                    "children": []
                }
                home_node['children'].append(shared_node)
            
            # 为每个用户创建主目录（包括admin）
            users = self._load_users()
            for user in users:
                user_exists = False
                for child in home_node['children']:
                    if not isinstance(child, dict):
                        continue
                    if child.get('name') == user and child.get('type') == 'dir':
                        user_exists = True
                        break
                if not user_exists:
                    user_node = {
                        "name": user, "type": "dir", "path": f"/home/{user}",
                        "created": self.get_current_time(), "modified": self.get_current_time(),
                        "children": []
                    }
                    home_node['children'].append(user_node)
            
            # 确保 /system 目录存在（用于存储加密信息等系统文件）
            system_exists = False
            for child in root_node['children']:
                if not isinstance(child, dict):
                    continue
                if child.get('name') == 'system' and child.get('type') == 'dir':
                    system_exists = True
                    break
            if not system_exists:
                system_node = {
                    "name": "system", "type": "dir", "path": "/system",
                    "created": self.get_current_time(), "modified": self.get_current_time(),
                    "children": []
                }
                root_node['children'].append(system_node)
        except Exception as e:
            print(f"创建用户目录失败: {e}")
            import traceback
            traceback.print_exc()

    def _load_users(self):
        """加载所有用户名列表"""
        if not os.path.exists(self.users_file):
            return []
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理不同的JSON格式
            if isinstance(data, dict):
                if 'users' in data and isinstance(data['users'], list):
                    # 格式: {"users": [{"username": "xxx", ...}, ...]}
                    return [user.get('username') for user in data['users'] if user.get('username')]
                else:
                    # 格式: {"username1": {...}, "username2": {...}}
                    return list(data.keys())
            elif isinstance(data, list):
                # 格式: [{"username": "xxx", ...}, ...]
                return [user.get('username') for user in data if user.get('username')]
            else:
                return []
        except Exception as e:
            print(f"加载用户列表失败: {e}")
            return []

    def save_file_system(self, fs_data=None):
        """保存文件系统数据"""
        if fs_data is None:
            fs_data = self.file_system
            
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            # 创建备份
            backup_file = self.fs_file + '.backup'
            if os.path.exists(self.fs_file):
                shutil.copy2(self.fs_file, backup_file)
            
            # 尝试序列化数据，检查是否有循环引用
            json_str = json.dumps(fs_data, indent=2, ensure_ascii=False)
            
            # 写入文件
            with open(self.fs_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
                
            # 如果成功，删除备份
            if os.path.exists(backup_file):
                os.remove(backup_file)
                
        except RecursionError as e:
            print(f"保存文件系统失败: 检测到循环引用 - {e}")
            # 尝试恢复备份
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, self.fs_file)
                print("已恢复备份文件")
        except Exception as e:
            print(f"保存文件系统失败: {e}")
            # 尝试恢复备份
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, self.fs_file)
                print("已恢复备份文件")
    
    def get_current_time(self) -> str:
        """获取当前时间字符串"""
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def load_users(self) -> Dict:
        """加载用户数据"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保返回的是字典格式
                if isinstance(data, dict):
                    return data
                else:
                    print("用户数据格式错误，返回空字典")
                    return {}
        except Exception as e:
            print(f"加载用户数据失败: {e}")
            return {}
    
    def verify_user_password(self, username: str, password: str) -> bool:
        """验证用户密码"""
        try:
            users_data = self.load_users()
            # 新的用户数据格式是字典：{"username": {"password": "哈希密码", ...}}
            if username in users_data:
                user_info = users_data[username]
                # 对输入的密码进行SHA256加密，然后与存储的哈希密码比较
                hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
                return user_info.get("password") == hashed_password
            return False
        except Exception as e:
            print(f"验证用户密码失败: {e}")
            return False
    
    def check_access_permission(self, current_user: str, target_path: str) -> bool:
        """检查访问权限"""
        # 管理员可以访问所有路径
        if self.is_admin(current_user):
            return True
            
        # 用户总是可以访问自己的目录
        if target_path == f"/home/{current_user}" or target_path.startswith(f"/home/{current_user}/"):
            return True
            
        # 用户总是可以访问共享目录
        if target_path == "/home/shared" or target_path.startswith("/home/shared/"):
            return True
            
        # 用户总是可以访问home目录（但只能看到自己的目录和共享目录）
        if target_path == "/home":
            return True
            
        # 其他情况需要密码验证
        return False
    
    def is_admin(self, username: str) -> bool:
        """检查用户是否为管理员"""
        try:
            users_data = self.load_users()
            # 新的用户数据格式是字典：{"username": {"role": "admin", ...}}
            if username in users_data:
                return users_data[username].get("role", "user") == "admin"
            return False
        except Exception as e:
            print(f"检查管理员权限失败: {e}")
            return False
    
    def create_user_directory(self, username: str) -> bool:
        """为用户创建目录"""
        try:
            home_dir = self.file_system["root"]["children"]["home"]
            if username not in home_dir["children"]:
                home_dir["children"][username] = {
                    "name": username,
                    "type": "dir",
                    "path": f"/home/{username}",
                    "created": self.get_current_time(),
                    "modified": self.get_current_time(),
                    "children": []
                }
                home_dir["modified"] = self.get_current_time()
                self.save_file_system()
                return True
            return False
        except Exception as e:
            print(f"创建用户目录失败: {e}")
            return False
    
    def get_directory_content(self, path: str, current_user: str = None, show_hidden: bool = False) -> Optional[List[Dict]]:
        """获取指定路径的目录内容，可选择是否显示隐藏文件"""
        parent_node = self._get_node_by_path(path)
        if not parent_node or parent_node.get("type") != "dir":
            return None
        
        # Permission check to view content
        if current_user and not self.check_access_permission(current_user, path):
            print(f"Access denied for {current_user} to path {path}")
            return None
        
        # Get all children and filter hidden items if needed
        all_children = list(parent_node.get("children", []))
        if not show_hidden:
            # Filter out hidden items
            visible_children = [child for child in all_children if not child.get('hidden', False)]
            return visible_children
        else:
            return all_children

    def create_item(self, path: str, item_name: str, item_type: str, content: str = "") -> bool:
        """通用创建文件或目录方法, 自动处理重名"""
        parent_node = self._get_node_by_path(path)
        if not parent_node or parent_node.get("type") != "dir":
            return False

        # Auto-rename if an item with the same name and type exists
        final_name = item_name
        counter = 1
        while self._find_child_in_node(parent_node, final_name, item_type) is not None:
            base_name, ext = os.path.splitext(item_name)
            final_name = f"{base_name} - 副本" if counter == 1 else f"{base_name} - 副本{counter}"
            if ext:
                final_name += ext
            counter += 1
        
        new_item_path = os.path.join(path, final_name).replace('\\', '/')
        if new_item_path.startswith('//'):
            new_item_path = new_item_path[1:]

        new_item = {
            "name": final_name,
            "type": item_type,
            "path": new_item_path,
            "created": self.get_current_time(),
            "modified": self.get_current_time(),
        }
        if item_type == 'dir':
            new_item["children"] = []
        else: # file
            new_item["content"] = content
            new_item["size"] = len(content)
        
        parent_node["children"].append(new_item)
        parent_node["modified"] = self.get_current_time()
        self.save_file_system()
        return True

    def create_file(self, path: str, filename: str, content: str = "", current_user: str = None) -> bool:
        success = self.create_item(path, filename, "file", content)
        if success and current_user:
            self.system_monitor.log_file_access(f"{path}/{filename}", "create", current_user)
        elif not success and current_user:
            self.system_monitor.log_file_access(f"{path}/{filename}", "create", current_user, False)
        return success

    def create_file_with_content(self, file_path: str, content: Dict, current_user: str = None) -> bool:
        """创建带有内容的文件"""
        try:
            # 解析路径
            path_parts = file_path.split('/')
            filename = path_parts[-1]
            parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else '/'
            
            # 检查权限
            if current_user and not self.check_access_permission(current_user, parent_path):
                return False
            
            # 获取父节点
            parent_node = self._get_node_by_path(parent_path)
            if not parent_node:
                return False
            
            # 检查是否已存在
            existing = self._find_child_in_node(parent_node, filename, "file")
            if existing:
                return False
            
            # 创建文件节点
            file_node = {
                "name": filename,
                "type": "file",
                "path": file_path,
                "content": content.get("content", ""),
                "size": content.get("size", 0),
                "created": self.get_current_time(),
                "modified": self.get_current_time(),
                "hidden": content.get("hidden", False)
            }
            
            # 添加特殊属性
            for key, value in content.items():
                if key not in ["name", "type", "path", "content", "size", "created", "modified", "hidden"]:
                    file_node[key] = value
            
            # 添加到父节点
            if "children" not in parent_node:
                parent_node["children"] = []
            parent_node["children"].append(file_node)
            
            # 保存文件系统
            self.save_file_system()
            return True
            
        except Exception as e:
            print(f"创建文件失败: {e}")
            return False

    def create_directory(self, path: str, dirname: str, current_user: str = None) -> bool:
        success = self.create_item(path, dirname, "dir")
        if success and current_user:
            self.system_monitor.log_file_access(f"{path}/{dirname}", "create_dir", current_user)
        elif not success and current_user:
            self.system_monitor.log_file_access(f"{path}/{dirname}", "create_dir", current_user, False)
        return success

    def delete_item(self, path: str, item_name: str, item_type: str, current_user: str = None) -> bool:
        if not self.check_access_permission(current_user, path): 
            if current_user:
                self.system_monitor.log_file_access(f"{path}/{item_name}", "delete", current_user, False)
            return False
        
        parent_node = self._get_node_by_path(path)
        if not parent_node:
            if current_user:
                self.system_monitor.log_file_access(f"{path}/{item_name}", "delete", current_user, False)
            return False
        
        child_info = self._find_child_in_node(parent_node, item_name, item_type)
        if not child_info:
            if current_user:
                self.system_monitor.log_file_access(f"{path}/{item_name}", "delete", current_user, False)
            return False
        
        index, child_node = child_info
        
        # 记录删除日志
        if current_user:
            self.system_monitor.log_file_access(f"{path}/{item_name}", "delete", current_user)
        
        # 如果是文件，从缓存中删除
        if item_type == "file":
            file_path = f"{path}/{item_name}"
            if file_path in self.system_monitor.file_cache:
                self.system_monitor.current_cache_size -= self.system_monitor.file_cache[file_path]['size']
                del self.system_monitor.file_cache[file_path]
        
        del parent_node['children'][index]
        parent_node['modified'] = self.get_current_time()
        self.save_file_system()
        return True

    def rename_item(self, path: str, old_name: str, new_name: str, item_type: str, current_user: str = None) -> bool:
        if not self.check_access_permission(current_user, path): return False
        
        parent_node = self._get_node_by_path(path)
        
        # Check if new name for the same type already exists
        if self._find_child_in_node(parent_node, new_name, item_type):
            return False # Or handle with auto-renaming
            
        child_info = self._find_child_in_node(parent_node, old_name, item_type)
        if not child_info:
            return False
            
        _, child_node = child_info
        
        # Update name and path
        child_node['name'] = new_name
        child_node['modified'] = self.get_current_time()
        
        # Important: must also recursively update path for all children if it's a directory
        def update_paths_recursive(node, old_base, new_base):
            node['path'] = node['path'].replace(old_base, new_base, 1)
            if node['type'] == 'dir':
                for child in node.get('children', []):
                    update_paths_recursive(child, old_base, new_base)

        old_item_path = child_node['path']
        new_item_path = os.path.join(path, new_name).replace('\\', '/')
        if new_item_path.startswith('//'):
            new_item_path = new_item_path[1:]

        update_paths_recursive(child_node, old_item_path, new_item_path)
        
        parent_node["modified"] = self.get_current_time()
        self.save_file_system()
        return True
    
    def write_file(self, path: str, filename: str, content: str, current_user: str = None) -> bool:
        # 添加调试信息
        print(f"write_file调试信息:")
        print(f"  路径: {path}")
        print(f"  文件名: {filename}")
        print(f"  用户: {current_user}")
        print(f"  内容长度: {len(content)}")
        
        if not self.check_access_permission(current_user, path): 
            print(f"  权限检查失败")
            if current_user:
                self.system_monitor.log_file_access(f"{path}/{filename}", "write", current_user, False)
            return False
        
        parent_node = self._get_node_by_path(path)
        if not parent_node:
            print(f"  父节点未找到")
            if current_user:
                self.system_monitor.log_file_access(f"{path}/{filename}", "write", current_user, False)
            return False
        
        child_info = self._find_child_in_node(parent_node, filename, 'file')
        if not child_info:
            print(f"  文件节点未找到")
            if current_user:
                self.system_monitor.log_file_access(f"{path}/{filename}", "write", current_user, False)
            return False
        
        _, child_node = child_info
        child_node['content'] = content
        child_node['size'] = len(content)
        child_node['modified'] = self.get_current_time()
        parent_node['modified'] = self.get_current_time()
        
        # 记录写入日志
        if current_user:
            self.system_monitor.log_file_access(f"{path}/{filename}", "write", current_user)
        
        # 更新缓存
        self.system_monitor.cache_file_content(f"{path}/{filename}", content)
        
        print(f"  准备保存到JSON文件")
        self.save_file_system()
        print(f"  保存完成")
        return True
    
    def get_file_content(self, file_path: str, current_user: str = None) -> Optional[str]:
        """获取文件内容"""
        try:
            # 记录访问日志
            if current_user:
                self.system_monitor.log_file_access(file_path, "read", current_user)
            
            # 先尝试从缓存获取
            cached_content = self.system_monitor.get_cached_content(file_path)
            if cached_content is not None:
                return cached_content
            
            # 解析路径
            path_parts = file_path.split('/')
            filename = path_parts[-1]
            parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else '/'
            
            # 检查权限
            if current_user and not self.check_access_permission(current_user, parent_path):
                if current_user:
                    self.system_monitor.log_file_access(file_path, "read", current_user, False)
                return None
            
            # 获取父节点
            parent_node = self._get_node_by_path(parent_path)
            if not parent_node:
                if current_user:
                    self.system_monitor.log_file_access(file_path, "read", current_user, False)
                return None
            
            # 查找文件
            result = self._find_child_in_node(parent_node, filename, "file")
            if not result:
                if current_user:
                    self.system_monitor.log_file_access(file_path, "read", current_user, False)
                return None
            
            _, file_node = result
            content = file_node.get("content", "")
            
            # 缓存文件内容
            self.system_monitor.cache_file_content(file_path, content)
            
            return content
            
        except Exception as e:
            print(f"获取文件内容失败: {e}")
            if current_user:
                self.system_monitor.log_file_access(file_path, "read", current_user, False)
            return None

    def get_item_info(self, item_path: str, current_user: str = None) -> Optional[Dict]:
        """获取项目信息"""
        try:
            # 解析路径
            path_parts = item_path.split('/')
            item_name = path_parts[-1]
            parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else '/'
            
            # 检查权限
            if current_user and not self.check_access_permission(current_user, parent_path):
                return None
            
            # 获取父节点
            parent_node = self._get_node_by_path(parent_path)
            if not parent_node:
                return None
            
            # 查找项目
            result = self._find_child_in_node(parent_node, item_name)
            if not result:
                return None
            
            _, item_node = result
            return item_node
            
        except Exception as e:
            print(f"获取项目信息失败: {e}")
            return None

    def read_file(self, file_path: str, current_user: str = None) -> Optional[str]:
        """读取文件内容（别名方法）"""
        return self.get_file_content(file_path, current_user)

    def _recursively_update_paths(self, node: Dict, new_base_path: str):
        """递归更新节点及其所有子节点的路径"""
        node['path'] = os.path.join(new_base_path, node['name']).replace('\\', '/')
        if node['path'].startswith('//'):
            node['path'] = node['path'][1:]
        
        node['modified'] = self.get_current_time()
        
        if node['type'] == 'dir':
            for child in node.get('children', []):
                self._recursively_update_paths(child, node['path'])

    def copy_items(self, source_path: str, items: List[Dict], current_user: str = None) -> bool:
        """将项目复制到剪贴板，items是包含name和type的字典列表"""
        if not self.check_access_permission(current_user, source_path):
            return False
            
        source_node = self._get_node_by_path(source_path)
        if not source_node:
            return False

        self.clipboard['type'] = 'copy'
        self.clipboard['source_path'] = source_path
        self.clipboard['items'] = []

        for item_info in items:
            child_info = self._find_child_in_node(source_node, item_info['name'], item_info['type'])
            if child_info:
                _, child_node = child_info
                self.clipboard['items'].append(copy.deepcopy(child_node))
        
        return len(self.clipboard['items']) > 0

    def cut_items(self, source_path: str, items: List[Dict], current_user: str = None) -> bool:
        """将项目剪切到剪贴板"""
        if not self.check_access_permission(current_user, source_path):
            return False
            
        is_copied = self.copy_items(source_path, items, current_user)
        if is_copied:
            self.clipboard['type'] = 'cut'
            return True
        return False

    def paste_items(self, target_path: str, current_user: str = None) -> bool:
        """粘贴剪贴板中的项目"""
        if not self.check_access_permission(current_user, target_path):
            return False
        if not self.clipboard['type'] or not self.clipboard['items']:
            return False
            
        target_node = self._get_node_by_path(target_path)
        if not target_node or target_node.get("type") != "dir":
            return False

        is_cut = self.clipboard['type'] == 'cut'
        source_path = self.clipboard['source_path']

        for item_snapshot in self.clipboard['items']:
            original_name = item_snapshot['name']
            item_type = item_snapshot['type']
            final_name = original_name
            
            # Auto-rename if an item with the same name and type exists in the target
            counter = 1
            while self._find_child_in_node(target_node, final_name, item_type):
                base_name, ext = os.path.splitext(original_name)
                final_name = f"{base_name} - 副本" if counter == 1 else f"{base_name} - 副本{counter}"
                if ext:
                    final_name += ext
                counter += 1
            
            # Update the name and recursively update all paths inside the snapshot
            item_snapshot['name'] = final_name
            self._recursively_update_paths(item_snapshot, target_path)

            # Add the (potentially renamed) item to the target node
            target_node['children'].append(item_snapshot)

        target_node['modified'] = self.get_current_time()

        # If it was a 'cut', remove the originals from the source
        if is_cut:
            source_node = self._get_node_by_path(source_path)
            if source_node:
                items_to_delete = self.clipboard['items'] # Use the original item info from clipboard
                
                indices_to_delete = []
                for item_to_delete in items_to_delete:
                    # We need the original name to find it in the source
                    child_info = self._find_child_in_node(source_node, item_to_delete['name'], item_to_delete['type'])
                    if child_info:
                        indices_to_delete.append(child_info[0])
                
                # Delete by index in reverse order to avoid index shifting issues
                for index in sorted(indices_to_delete, reverse=True):
                    del source_node['children'][index]

                source_node['modified'] = self.get_current_time()
            self.clear_clipboard()

        self.save_file_system()
        return True

    def clear_clipboard(self):
        self.clipboard = {'type': None, 'items': [], 'source_path': None}

    def get_clipboard_info(self) -> Dict:
        """获取剪贴板信息"""
        return {
             'type': self.clipboard['type'],
             'count': len(self.clipboard['items']),
             'source_path': self.clipboard.get('source_path'),
             'items': [f"{item['name']} ({item['type']})" for item in self.clipboard.get('items', [])]
         }

    def get_full_tree(self):
        """返回整个文件系统的树状结构数据"""
        # The structure is already a tree
        return self.file_system 

    def set_item_hidden(self, path: str, item_name: str, item_type: str, hidden: bool, current_user: str = None) -> bool:
        """设置文件或文件夹的隐藏状态"""
        if not self.check_access_permission(current_user, path): return False
        
        parent_node = self._get_node_by_path(path)
        child_info = self._find_child_in_node(parent_node, item_name, item_type)
        if not child_info:
            return False
            
        _, child_node = child_info
        child_node['hidden'] = hidden
        child_node['modified'] = self.get_current_time()
        parent_node['modified'] = self.get_current_time()
        self.save_file_system()
        return True

    def is_item_hidden(self, path: str, item_name: str, item_type: str) -> bool:
        """检查文件或文件夹是否隐藏"""
        parent_node = self._get_node_by_path(path)
        if not parent_node:
            return False
            
        child_info = self._find_child_in_node(parent_node, item_name, item_type)
        if not child_info:
            return False
            
        _, child_node = child_info
        return child_node.get('hidden', False)

    def hide_item(self, path: str, item_name: str, item_type: str, current_user: str = None) -> bool:
        """隐藏文件或文件夹"""
        return self.set_item_hidden(path, item_name, item_type, True, current_user)

    def unhide_item(self, path: str, item_name: str, item_type: str, current_user: str = None) -> bool:
        """显示文件或文件夹（取消隐藏）"""
        return self.set_item_hidden(path, item_name, item_type, False, current_user)

    def copy_item(self, source_path: str, target_path: str, current_user: str = None) -> bool:
        """复制单个项目"""
        try:
            # 获取源项目信息
            source_info = self.get_item_info(source_path, current_user)
            if not source_info:
                return False
            
            # 解析目标路径
            target_parts = target_path.split('/')
            target_name = target_parts[-1]
            target_parent_path = '/'.join(target_parts[:-1]) if len(target_parts) > 1 else '/'
            
            # 检查目标路径权限
            if current_user and not self.check_access_permission(current_user, target_parent_path):
                return False
            
            # 获取目标父节点
            target_parent_node = self._get_node_by_path(target_parent_path)
            if not target_parent_node:
                return False
            
            # 创建新的项目节点
            new_item = copy.deepcopy(source_info)
            new_item["name"] = target_name
            new_item["path"] = target_path
            new_item["modified"] = self.get_current_time()
            
            # 如果是目录，递归更新子项目的路径
            if new_item["type"] == "dir":
                self._recursively_update_paths(new_item, target_path)
            
            # 添加到目标父节点
            if "children" not in target_parent_node:
                target_parent_node["children"] = []
            target_parent_node["children"].append(new_item)
            
            # 保存文件系统
            self.save_file_system()
            return True
            
        except Exception as e:
            print(f"复制项目失败: {e}")
            return False

    def move_item(self, source_path: str, target_path: str, current_user: str = None) -> bool:
        """移动单个项目"""
        try:
            # 先复制
            if not self.copy_item(source_path, target_path, current_user):
                return False
            
            # 再删除源项目
            source_parts = source_path.split('/')
            source_name = source_parts[-1]
            source_parent_path = '/'.join(source_parts[:-1]) if len(source_parts) > 1 else '/'
            
            return self.delete_item(source_parent_path, source_name, "file" if source_path.endswith('.txt') else "dir", current_user)
            
        except Exception as e:
            print(f"移动项目失败: {e}")
            return False 