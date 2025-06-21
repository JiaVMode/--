##########################################
#             系统监控模块
#             作者：李嘉
#           学号：3123009043
#          班级：23人工智能1班
#         指导教师：苏畅、李剑锋
###########################################
"""
系统监控模块
包含磁盘使用统计、文件访问日志和系统性能监控
"""

import os
import json
import time
import psutil
import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, file_system):
        self.file_system = file_system
        self.log_file = os.path.join(file_system.data_dir, 'system_log.json')
        self.cache_file = os.path.join(file_system.data_dir, 'file_cache.json')
        self.index_file = os.path.join(file_system.data_dir, 'file_index.json')
        
        # 文件访问日志
        self.access_log = deque(maxlen=1000)  # 最多保存1000条记录
        
        # 文件缓存
        self.file_cache = {}
        self.cache_size_limit = 50 * 1024 * 1024  # 50MB缓存限制
        self.current_cache_size = 0
        
        # 文件索引
        self.file_index = {}
        
        # 性能监控数据
        self.performance_history = deque(maxlen=100)  # 保存最近100次监控数据
        
        # 加载现有数据
        self.load_data()
        
        # 启动后台索引
        self.start_background_indexing()
    
    def load_data(self):
        """加载现有数据"""
        # 加载访问日志
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.access_log = deque(data.get('access_log', []), maxlen=1000)
        except Exception as e:
            print(f"加载访问日志失败: {e}")
        
        # 加载文件缓存
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.file_cache = data.get('cache', {})
                    self.current_cache_size = data.get('size', 0)
        except Exception as e:
            print(f"加载文件缓存失败: {e}")
        
        # 加载文件索引
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.file_index = json.load(f)
        except Exception as e:
            print(f"加载文件索引失败: {e}")
    
    def save_data(self):
        """保存数据"""
        # 保存访问日志
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'access_log': list(self.access_log),
                    'last_update': datetime.datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存访问日志失败: {e}")
        
        # 保存文件缓存
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'cache': self.file_cache,
                    'size': self.current_cache_size,
                    'last_update': datetime.datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存文件缓存失败: {e}")
        
        # 保存文件索引
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存文件索引失败: {e}")
    
    def log_file_access(self, file_path: str, operation: str, username: str, success: bool = True):
        """记录文件访问日志"""
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'file_path': file_path,
            'operation': operation,  # read, write, delete, create, etc.
            'username': username,
            'success': success
        }
        self.access_log.append(log_entry)
    
    def get_disk_usage_stats(self) -> Dict:
        """获取磁盘使用统计"""
        stats = {
            'total_files': 0,
            'total_dirs': 0,
            'total_size': 0,
            'directory_stats': {},
            'file_type_stats': {},
            'user_stats': {}
        }
        
        def analyze_directory(node, path):
            """递归分析目录"""
            if not isinstance(node, dict):
                return
            
            if node.get('type') == 'dir':
                stats['total_dirs'] += 1
                dir_name = node.get('name', '')
                
                # 按目录统计
                if path not in stats['directory_stats']:
                    stats['directory_stats'][path] = {
                        'files': 0,
                        'dirs': 0,
                        'size': 0
                    }
                
                # 分析子项
                for child in node.get('children', []):
                    if isinstance(child, dict):
                        child_path = child.get('path', '')
                        if child.get('type') == 'file':
                            stats['total_files'] += 1
                            stats['directory_stats'][path]['files'] += 1
                            
                            # 文件大小
                            file_size = child.get('size', 0)
                            stats['total_size'] += file_size
                            stats['directory_stats'][path]['size'] += file_size
                            
                            # 文件类型统计
                            file_name = child.get('name', '')
                            if '.' in file_name:
                                ext = file_name.split('.')[-1].lower()
                                stats['file_type_stats'][ext] = stats['file_type_stats'].get(ext, 0) + 1
                            
                            # 用户统计
                            owner = child.get('owner', 'unknown')
                            if owner not in stats['user_stats']:
                                stats['user_stats'][owner] = {
                                    'files': 0,
                                    'size': 0
                                }
                            stats['user_stats'][owner]['files'] += 1
                            stats['user_stats'][owner]['size'] += file_size
                        else:
                            stats['directory_stats'][path]['dirs'] += 1
                            analyze_directory(child, child_path)
        
        # 分析根目录
        root_node = self.file_system.file_system.get('root')
        if root_node:
            analyze_directory(root_node, '/')
        
        return stats
    
    def get_performance_stats(self) -> Dict:
        """获取系统性能统计"""
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 计算缓存命中率
        cache_hits = getattr(self, 'cache_hits', 0)
        cache_misses = getattr(self, 'cache_misses', 0)
        total_requests = cache_hits + cache_misses
        cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        performance_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'memory_available': memory.available,
            'memory_total': memory.total,
            'disk_usage': disk.percent,
            'disk_free': disk.free,
            'disk_total': disk.total,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': self.current_cache_size,
            'cache_entries': len(self.file_cache),
            'index_entries': len(self.file_index)
        }
        
        self.performance_history.append(performance_data)
        return performance_data
    
    def get_access_log_summary(self, hours: int = 24) -> Dict:
        """获取访问日志摘要"""
        now = datetime.datetime.now()
        cutoff_time = now - datetime.timedelta(hours=hours)
        
        recent_logs = []
        for log in self.access_log:
            try:
                log_time = datetime.datetime.fromisoformat(log['timestamp'])
                if log_time >= cutoff_time:
                    recent_logs.append(log)
            except:
                continue
        
        # 统计操作类型
        operation_stats = defaultdict(int)
        user_stats = defaultdict(int)
        file_stats = defaultdict(int)
        
        for log in recent_logs:
            operation_stats[log['operation']] += 1
            user_stats[log['username']] += 1
            file_stats[log['file_path']] += 1
        
        return {
            'total_operations': len(recent_logs),
            'operation_stats': dict(operation_stats),
            'user_stats': dict(user_stats),
            'most_accessed_files': sorted(file_stats.items(), key=lambda x: x[1], reverse=True)[:10],
            'time_range': f"最近{hours}小时"
        }
    
    def cache_file_content(self, file_path: str, content: str) -> bool:
        """缓存文件内容"""
        content_size = len(content.encode('utf-8'))
        
        # 检查缓存大小限制
        if self.current_cache_size + content_size > self.cache_size_limit:
            # 清理最旧的缓存项
            self.cleanup_cache()
        
        # 如果仍然超出限制，不缓存
        if self.current_cache_size + content_size > self.cache_size_limit:
            return False
        
        # 添加到缓存
        self.file_cache[file_path] = {
            'content': content,
            'size': content_size,
            'timestamp': datetime.datetime.now().isoformat(),
            'access_count': 0
        }
        self.current_cache_size += content_size
        return True
    
    def get_cached_content(self, file_path: str) -> Optional[str]:
        """获取缓存的文件内容"""
        if file_path in self.file_cache:
            self.file_cache[file_path]['access_count'] += 1
            self.cache_hits = getattr(self, 'cache_hits', 0) + 1
            return self.file_cache[file_path]['content']
        
        self.cache_misses = getattr(self, 'cache_misses', 0) + 1
        return None
    
    def cleanup_cache(self):
        """清理缓存"""
        if not self.file_cache:
            return
        
        # 按访问次数和时间排序，删除最不常用的
        sorted_cache = sorted(
            self.file_cache.items(),
            key=lambda x: (x[1]['access_count'], x[1]['timestamp'])
        )
        
        # 删除前20%的缓存项
        items_to_remove = int(len(sorted_cache) * 0.2)
        for i in range(items_to_remove):
            file_path, cache_data = sorted_cache[i]
            self.current_cache_size -= cache_data['size']
            del self.file_cache[file_path]
    
    def start_background_indexing(self):
        """启动后台索引"""
        # 这里可以启动一个线程来定期重建索引
        # 为了简化，我们在这里直接构建索引
        self.build_file_index()
    
    def build_file_index(self):
        """构建文件索引"""
        self.file_index = {}
        
        def index_directory(node, path):
            """递归索引目录"""
            if not isinstance(node, dict):
                return
            
            if node.get('type') == 'file':
                file_name = node.get('name', '').lower()
                file_path = node.get('path', '')
                
                # 按文件名索引
                if file_name not in self.file_index:
                    self.file_index[file_name] = []
                self.file_index[file_name].append(file_path)
                
                # 按扩展名索引
                if '.' in file_name:
                    ext = file_name.split('.')[-1]
                    ext_key = f"*.{ext}"
                    if ext_key not in self.file_index:
                        self.file_index[ext_key] = []
                    self.file_index[ext_key].append(file_path)
            
            # 递归处理子项
            for child in node.get('children', []):
                if isinstance(child, dict):
                    child_path = child.get('path', '')
                    index_directory(child, child_path)
        
        # 索引根目录
        root_node = self.file_system.file_system.get('root')
        if root_node:
            index_directory(root_node, '/')
    
    def search_files_fast(self, query: str) -> List[str]:
        """快速文件搜索（使用索引）"""
        query = query.lower()
        results = []
        
        # 精确匹配
        if query in self.file_index:
            results.extend(self.file_index[query])
        
        # 模糊匹配
        for file_name, file_paths in self.file_index.items():
            if query in file_name and file_name != query:
                results.extend(file_paths)
        
        return list(set(results))  # 去重
    
    def get_system_health_report(self) -> Dict:
        """获取系统健康报告"""
        performance = self.get_performance_stats()
        disk_usage = self.get_disk_usage_stats()
        access_summary = self.get_access_log_summary()
        
        # 健康评分
        health_score = 100
        
        # CPU使用率评分
        if performance['cpu_usage'] > 80:
            health_score -= 20
        elif performance['cpu_usage'] > 60:
            health_score -= 10
        
        # 内存使用率评分
        if performance['memory_usage'] > 90:
            health_score -= 20
        elif performance['memory_usage'] > 80:
            health_score -= 10
        
        # 缓存命中率评分
        if performance['cache_hit_rate'] < 50:
            health_score -= 15
        elif performance['cache_hit_rate'] < 70:
            health_score -= 5
        
        return {
            'health_score': max(0, health_score),
            'performance': performance,
            'disk_usage': disk_usage,
            'access_summary': access_summary,
            'recommendations': self.get_recommendations(performance, disk_usage)
        }
    
    def get_recommendations(self, performance: Dict, disk_usage: Dict) -> List[str]:
        """获取系统优化建议"""
        recommendations = []
        
        if performance['cpu_usage'] > 80:
            recommendations.append("CPU使用率过高，建议关闭不必要的程序")
        
        if performance['memory_usage'] > 90:
            recommendations.append("内存使用率过高，建议清理内存或增加内存")
        
        if performance['cache_hit_rate'] < 50:
            recommendations.append("缓存命中率较低，建议增加缓存大小或优化访问模式")
        
        if disk_usage['total_size'] > 1024 * 1024 * 1024:  # 1GB
            recommendations.append("文件系统较大，建议定期清理无用文件")
        
        return recommendations
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
        
        # 清理访问日志
        new_logs = []
        for log in self.access_log:
            try:
                log_time = datetime.datetime.fromisoformat(log['timestamp'])
                if log_time >= cutoff_time:
                    new_logs.append(log)
            except:
                continue
        
        self.access_log = deque(new_logs, maxlen=1000)
        
        # 保存更新后的数据
        self.save_data() 