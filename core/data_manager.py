# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from core.json_utils import read_json_file, write_json_file
from core.sqlite_manager import SQLiteManager


class DataManager:
    def __init__(self, data_file='data/tasks.json'):
        """初始化数据管理器"""
        self.data_file = data_file
        self.sqlite_manager = SQLiteManager()
        self.tasks = []
        
        # 检查JSON文件是否存在，如果存在则迁移到SQLite
        if os.path.exists(self.data_file):
            self.migrate_json_to_sqlite()
    
    def migrate_json_to_sqlite(self):
        """将JSON数据迁移到SQLite"""
        try:
            # 读取JSON数据
            json_data = read_json_file(self.data_file)
            
            # 将JSON数据迁移到SQLite
            if self.sqlite_manager.json_to_sqlite(json_data):
                print("JSON数据已成功迁移到SQLite")
        except Exception as e:
            print(f"JSON数据迁移失败: {e}")
    
    def load_tasks(self):
        """从SQLite加载任务数据"""
        try:
            # 从SQLite获取任务数据
            tasks = self.sqlite_manager.get_all_tasks()
            
            # 如果SQLite中没有数据，尝试从JSON文件读取
            if not tasks:
                json_data = read_json_file(self.data_file)
                if json_data:
                    tasks = json_data
            
            # 更新内存中的任务列表
            self.tasks = tasks
            return tasks
        except Exception as e:
            print(f"加载任务失败: {e}")
            return []
    
    def save_tasks(self, tasks):
        """保存任务数据到SQLite和JSON"""
        try:
            # 更新内存中的任务列表
            self.tasks = tasks
            
            # 保存到SQLite
            if self.sqlite_manager.save_tasks(tasks):
                print("任务已成功保存到SQLite")
            
            # 保存到JSON（保持兼容）
            if write_json_file(self.data_file, tasks):
                print("任务已成功保存到JSON文件")
                return True
            return False
        except Exception as e:
            print(f"保存任务失败: {e}")
            return False
    
    def get_tasks_after_time(self, time_str):
        """获取指定时间之后修改的任务"""
        return self.sqlite_manager.get_tasks_after_time(time_str)
    
    def insert_task(self, task_info):
        """插入新任务"""
        return self.sqlite_manager.insert_task(task_info)
    
    def update_task(self, task_id, task_info):
        """更新任务"""
        return self.sqlite_manager.update_task(task_id, task_info)
    
    def delete_task(self, task_id):
        """删除任务"""
        return self.sqlite_manager.delete_task(task_id)
    
    def mark_task_done(self, task_id):
        """标记任务为完成"""
        return self.sqlite_manager.mark_task_done(task_id)
    
    def get_all_tasks(self):
        """获取所有任务"""
        return self.sqlite_manager.get_all_tasks()
    
    def import_phone_data(self, phone_tasks):
        """导入手机端数据"""
        return self.sqlite_manager.import_phone_data(phone_tasks)