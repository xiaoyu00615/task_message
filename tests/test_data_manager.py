#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataManager类的单元测试
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch
from core.data_manager import DataManager


class TestDataManager(unittest.TestCase):
    """测试DataManager类的功能"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建临时目录和文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_tasks_path = os.path.join(self.temp_dir.name, 'tasks.json')
        # 初始化数据管理器，使用临时路径
        self.data_manager = DataManager(self.temp_tasks_path)
    
    def tearDown(self):
        """每个测试后的清理"""
        # 清理临时目录
        self.temp_dir.cleanup()
    
    def test_load_empty_data(self):
        """测试加载空数据（文件不存在时）"""
        # 确保测试前数据文件不存在
        if os.path.exists(self.temp_tasks_path):
            os.remove(self.temp_tasks_path)
        
        # 加载数据
        data = self.data_manager.load_tasks()
        
        # 验证返回的是默认数据结构
        self.assertEqual(data, self.data_manager.default_data)
    
    @patch('PyQt5.QtWidgets.QMessageBox.warning')
    def test_load_invalid_json(self, mock_warning):
        """测试加载格式错误的JSON文件"""
        # 创建一个格式错误的JSON文件
        with open(self.temp_tasks_path, 'w', encoding='utf-8') as f:
            f.write('这不是有效的JSON格式')
        
        # 加载数据
        data = self.data_manager.load_tasks()
        
        # 验证返回的是默认数据
        self.assertEqual(data, self.data_manager.default_data)
        # 验证显示了警告消息
        mock_warning.assert_called_once()
    
    def test_load_incomplete_data(self):
        """测试加载缺少某些键的数据"""
        # 创建只有部分键的数据
        incomplete_data = {
            "todo": [
                {"name": "测试任务", "deadline": "2023-12-31 23:59", "create_time": "2023-12-01 10:00"}
            ]
            # 故意缺少 done 和 overdue 键
        }
        
        # 保存不完整数据
        with open(self.temp_tasks_path, 'w', encoding='utf-8') as f:
            json.dump(incomplete_data, f, ensure_ascii=False, indent=2)
        
        # 加载数据
        data = self.data_manager.load_tasks()
        
        # 验证所有必要的键都存在
        self.assertIn('todo', data)
        self.assertIn('done', data)
        self.assertIn('overdue', data)
        # 验证原始数据被保留
        self.assertEqual(len(data['todo']), 1)
        # 验证缺少的键被初始化为空列表
        self.assertEqual(data['done'], [])
        self.assertEqual(data['overdue'], [])
    
    def test_save_and_load_tasks(self):
        """测试保存和加载任务数据"""
        # 创建测试数据
        test_data = {
            "todo": [
                {"name": "测试任务1", "deadline": "2023-12-31 23:59", "create_time": "2023-12-01 10:00"},
                {"name": "测试任务2", "deadline": "2023-12-25 18:00", "create_time": "2023-12-02 14:00", 
                 "subtasks": [{"text": "子任务1", "completed": False}, {"text": "子任务2", "completed": True}]}
            ],
            "done": [],
            "overdue": []
        }
        
        # 保存数据
        success = self.data_manager.save_tasks(test_data)
        
        # 验证保存成功
        self.assertTrue(success)
        
        # 重新加载数据
        loaded_data = self.data_manager.load_tasks()
        
        # 验证数据被正确保存和加载
        self.assertIn('todo', loaded_data)
        self.assertEqual(len(loaded_data['todo']), 2)
        self.assertEqual(loaded_data['todo'][0]['name'], '测试任务1')
        self.assertEqual(loaded_data['todo'][1]['name'], '测试任务2')
        # 验证subtasks被正确处理
        self.assertIn('subtasks', loaded_data['todo'][1])
        self.assertEqual(len(loaded_data['todo'][1]['subtasks']), 2)
    
    def test_backup_data(self):
        """测试数据备份功能"""
        # 创建测试数据
        test_data = {
            "todo": [{"name": "测试任务", "deadline": "2023-12-31 23:59", "create_time": "2023-12-01 10:00"}],
            "done": [],
            "overdue": []
        }
        
        # 先保存数据
        self.data_manager.save_tasks(test_data)
        
        # 执行备份
        backup_success = self.data_manager.backup_data()
        
        # 验证备份成功
        self.assertTrue(backup_success)
        
        # 验证备份文件存在
        backup_path = f"{self.temp_tasks_path}.bak"
        self.assertTrue(os.path.exists(backup_path))
        
        # 验证备份文件内容正确
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        self.assertIn('todo', backup_data)
        self.assertEqual(len(backup_data['todo']), 1)
    
    def test_save_with_missing_required_fields(self):
        """测试保存缺少必要字段的任务数据"""
        # 创建缺少必要字段的测试数据
        test_data = {
            "todo": [
                # 缺少deadline字段
                {"name": "测试任务1", "create_time": "2023-12-01 10:00"},
                # 缺少name字段
                {"deadline": "2023-12-25 18:00", "create_time": "2023-12-02 14:00"}
            ],
            "done": [],
            "overdue": []
        }
        
        # 保存数据
        success = self.data_manager.save_tasks(test_data)
        
        # 验证保存成功
        self.assertTrue(success)
        
        # 重新加载数据
        loaded_data = self.data_manager.load_tasks()
        
        # 验证缺少的字段有默认值
        self.assertEqual(len(loaded_data['todo']), 2)
        self.assertIn('deadline', loaded_data['todo'][0])
        self.assertIn('name', loaded_data['todo'][1])
    
    def test_compatibility_with_old_format_subtasks(self):
        """测试与旧格式（字符串列表）subtasks的兼容性"""
        # 创建使用旧格式subtasks的测试数据
        test_data = {
            "todo": [
                {"name": "测试任务", "deadline": "2023-12-31 23:59", "create_time": "2023-12-01 10:00", 
                 "subtasks": ["子任务1", "子任务2"]}  # 旧格式：字符串列表
            ],
            "done": [],
            "overdue": []
        }
        
        # 保存数据
        success = self.data_manager.save_tasks(test_data)
        
        # 验证保存成功
        self.assertTrue(success)
        
        # 重新加载数据
        loaded_data = self.data_manager.load_tasks()
        
        # 验证旧格式subtasks被正确转换为新格式
        self.assertIn('subtasks', loaded_data['todo'][0])
        self.assertEqual(len(loaded_data['todo'][0]['subtasks']), 2)
        self.assertIsInstance(loaded_data['todo'][0]['subtasks'][0], dict)
        self.assertEqual(loaded_data['todo'][0]['subtasks'][0]['text'], '子任务1')
        self.assertEqual(loaded_data['todo'][0]['subtasks'][0]['completed'], False)


if __name__ == '__main__':
    unittest.main()
