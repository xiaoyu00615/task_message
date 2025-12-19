#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaskHandler类的单元测试
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import time
from core.task_handler import TaskHandler


class TestTaskHandler(unittest.TestCase):
    """测试TaskHandler类的功能"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建模拟的数据管理器
        self.mock_data_manager = Mock()
        
        # 模拟加载的数据
        self.mock_data = {
            "todo": [],
            "done": [],
            "overdue": []
        }
        self.mock_data_manager.load_tasks.return_value = self.mock_data
        self.mock_data_manager.save_tasks.return_value = True
        self.mock_data_manager.backup_data.return_value = True
        
        # 补丁datetime.now和time.strftime以获取确定性的时间值
        self.now_patcher = patch('core.task_handler.datetime')
        self.time_patcher = patch('core.task_handler.time')
        self.mock_datetime = self.now_patcher.start()
        self.mock_time = self.time_patcher.start()
        
        # 设置固定的当前时间
        self.fixed_now = datetime(2023, 12, 15, 10, 0, 0)
        self.mock_datetime.now.return_value = self.fixed_now
        self.mock_time.strftime.return_value = "2023-12-15 10:00:00"
        
        # 初始化任务处理器
        with patch('core.task_handler.DataImportExport'):
            self.task_handler = TaskHandler(self.mock_data_manager)
    
    def tearDown(self):
        """每个测试后的清理"""
        # 停止补丁
        self.now_patcher.stop()
        self.time_patcher.stop()
    
    def test_calculate_time_remaining_no_deadline(self):
        """测试计算无截止日期任务的剩余时间"""
        task = {"deadline": "无截止日期"}
        result = self.task_handler.calculate_time_remaining(task)
        self.assertEqual(result, "无截止日期")
    
    def test_calculate_time_remaining_future(self):
        """测试计算未来任务的剩余时间"""
        task = {"deadline": "2023-12-25 18:00"}
        result = self.task_handler.calculate_time_remaining(task)
        self.assertIn("剩余", result)
        self.assertIn("10天", result)  # 从12月15日到12月25日
    
    def test_calculate_time_remaining_overdue(self):
        """测试计算已超时任务的剩余时间"""
        task = {"deadline": "2023-12-01 10:00"}
        result = self.task_handler.calculate_time_remaining(task)
        self.assertIn("已超时", result)
        self.assertIn("14天", result)  # 从12月1日到12月15日
    
    def test_add_task_success(self):
        """测试成功添加任务"""
        task_data = {
            "name": "测试任务",
            "deadline": "2023-12-31 23:59"
        }
        result = self.task_handler.add_task(task_data)
        
        self.assertTrue(result)
        self.assertEqual(len(self.task_handler.tasks['todo']), 1)
        self.assertEqual(self.task_handler.tasks['todo'][0]['name'], "测试任务")
        self.assertEqual(self.task_handler.tasks['todo'][0]['deadline'], "2023-12-31 23:59")
        self.assertIn('create_time', self.task_handler.tasks['todo'][0])
        self.assertIn('last_modified', self.task_handler.tasks['todo'][0])
        
        # 验证调用了数据管理器的方法
        self.mock_data_manager.backup_data.assert_called()
        self.mock_data_manager.save_tasks.assert_called()
    
    def test_add_task_with_subtasks(self):
        """测试添加带有子任务的任务"""
        task_data = {
            "name": "测试任务",
            "deadline": "2023-12-31 23:59",
            "subtasks": [
                {"text": "子任务1", "completed": False},
                {"text": "子任务2", "completed": True}
            ]
        }
        result = self.task_handler.add_task(task_data)
        
        self.assertTrue(result)
        self.assertEqual(len(self.task_handler.tasks['todo']), 1)
        self.assertEqual(len(self.task_handler.tasks['todo'][0]['subtasks']), 2)
        self.assertEqual(self.task_handler.tasks['todo'][0]['subtasks'][0]['text'], "子任务1")
        self.assertEqual(self.task_handler.tasks['todo'][0]['subtasks'][1]['completed'], True)
    
    def test_add_task_with_old_format_subtasks(self):
        """测试添加带有旧格式子任务的任务"""
        task_data = {
            "name": "测试任务",
            "deadline": "2023-12-31 23:59",
            "subtasks": ["子任务1", "子任务2"]
        }
        result = self.task_handler.add_task(task_data)
        
        self.assertTrue(result)
        self.assertEqual(len(self.task_handler.tasks['todo'][0]['subtasks']), 2)
        # 验证子任务被转换为新格式
        self.assertIsInstance(self.task_handler.tasks['todo'][0]['subtasks'][0], dict)
        self.assertEqual(self.task_handler.tasks['todo'][0]['subtasks'][0]['text'], "子任务1")
        self.assertEqual(self.task_handler.tasks['todo'][0]['subtasks'][0]['completed'], False)
    
    def test_add_task_invalid_data(self):
        """测试添加无效数据类型的任务"""
        result = self.task_handler.add_task("这不是一个字典")
        self.assertFalse(result)
        self.assertEqual(len(self.task_handler.tasks['todo']), 0)
    
    def test_mark_as_done_success(self):
        """测试成功标记任务为已完成"""
        # 添加一个测试任务
        test_task = {"name": "测试任务", "deadline": "2023-12-31 23:59"}
        self.task_handler.tasks['todo'].append(test_task)
        
        # 标记为完成
        result = self.task_handler.mark_as_done('todo', 0)
        
        self.assertTrue(result)
        self.assertEqual(len(self.task_handler.tasks['todo']), 0)
        self.assertEqual(len(self.task_handler.tasks['done']), 1)
        self.assertEqual(self.task_handler.tasks['done'][0]['name'], "测试任务")
        self.assertIn('done_time', self.task_handler.tasks['done'][0])
        
        # 验证调用了数据管理器的方法
        self.mock_data_manager.backup_data.assert_called()
        self.mock_data_manager.save_tasks.assert_called()
    
    def test_mark_as_done_invalid_task_type(self):
        """测试标记无效任务类型的任务为已完成"""
        result = self.task_handler.mark_as_done('invalid_type', 0)
        self.assertFalse(result)
    
    def test_mark_as_done_invalid_index(self):
        """测试标记无效索引的任务为已完成"""
        result = self.task_handler.mark_as_done('todo', 100)  # 索引超出范围
        self.assertFalse(result)
    
    def test_delete_task_success(self):
        """测试成功删除任务"""
        # 添加一个测试任务
        test_task = {"name": "测试任务", "deadline": "2023-12-31 23:59"}
        self.task_handler.tasks['todo'].append(test_task)
        
        # 删除任务
        result = self.task_handler.delete_task('todo', 0)
        
        self.assertTrue(result)
        self.assertEqual(len(self.task_handler.tasks['todo']), 0)
        
        # 验证调用了数据管理器的方法
        self.mock_data_manager.backup_data.assert_called()
        self.mock_data_manager.save_tasks.assert_called()
    
    def test_delete_task_invalid_task_type(self):
        """测试删除无效任务类型的任务"""
        result = self.task_handler.delete_task('invalid_type', 0)
        self.assertFalse(result)
    
    def test_delete_task_invalid_index(self):
        """测试删除无效索引的任务"""
        result = self.task_handler.delete_task('todo', 100)  # 索引超出范围
        self.assertFalse(result)
    
    def test_update_task_success(self):
        """测试成功更新任务"""
        # 添加一个测试任务
        test_task = {
            "name": "旧任务名",
            "deadline": "2023-12-31 23:59",
            "create_time": "2023-12-01 10:00:00"
        }
        self.task_handler.tasks['todo'].append(test_task)
        
        # 更新任务
        new_task_data = {
            "name": "新任务名",
            "deadline": "2024-01-31 23:59",
            "subtasks": [{"text": "新子任务", "completed": False}]
        }
        result = self.task_handler.update_task('todo', 0, new_task_data)
        
        self.assertTrue(result)
        self.assertEqual(self.task_handler.tasks['todo'][0]['name'], "新任务名")
        self.assertEqual(self.task_handler.tasks['todo'][0]['deadline'], "2024-01-31 23:59")
        self.assertEqual(len(self.task_handler.tasks['todo'][0].get('subtasks', [])), 1)
        
        # 验证原始创建时间保留
        self.assertEqual(self.task_handler.tasks['todo'][0]['create_time'], "2023-12-01 10:00:00")
    
    def test_update_task_invalid_data(self):
        """测试更新任务时传入无效数据"""
        # 添加一个测试任务
        test_task = {"name": "测试任务", "deadline": "2023-12-31 23:59"}
        self.task_handler.tasks['todo'].append(test_task)
        
        # 传入非字典类型数据
        result = self.task_handler.update_task('todo', 0, "这不是一个字典")
        self.assertFalse(result)
    
    def test_check_overdue_tasks(self):
        """测试检查超时任务"""
        # 添加一个超时任务和一个未超时任务
        overdue_task = {"name": "超时任务", "deadline": "2023-12-01 10:00"}
        future_task = {"name": "未超时任务", "deadline": "2023-12-31 23:59"}
        self.task_handler.tasks['todo'].extend([overdue_task, future_task])
        
        # 调用检查超时任务方法
        with patch.object(self.task_handler, 'auto_promote_urgency'):
            # 因为我们只关心超时检查，所以模拟auto_promote_urgency方法
            self.task_handler.check_overdue_tasks()
        
        # 验证任务正确分类
        self.assertEqual(len(self.task_handler.tasks['todo']), 1)  # 只保留未超时任务
        self.assertEqual(len(self.task_handler.tasks['overdue']), 1)  # 超时任务被移到overdue列表
        self.assertEqual(self.task_handler.tasks['overdue'][0]['name'], "超时任务")
    
    @patch('PyQt5.QtWidgets.QMessageBox.information')
    def test_check_overdue_tasks_with_notification(self, mock_message_box):
        """测试检查超时任务并显示通知"""
        # 添加一个超时任务
        overdue_task = {"name": "超时任务", "deadline": "2023-12-01 10:00"}
        self.task_handler.tasks['todo'].append(overdue_task)
        
        # 调用检查超时任务方法并模拟设置中启用了通知
        with patch.object(self.task_handler, 'auto_promote_urgency'):
            with patch.dict(self.task_handler.tasks, {'notification_shown': False}):
                self.task_handler.check_overdue_tasks()
        
        # 验证任务被移动到overdue列表
        self.assertEqual(len(self.task_handler.tasks['overdue']), 1)
        # 验证通知消息被调用
        mock_message_box.assert_called_once()


if __name__ == '__main__':
    unittest.main()
