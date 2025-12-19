#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConfigManager类的单元测试
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch
from core.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """测试ConfigManager类的功能"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建临时目录和文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_config_path = os.path.join(self.temp_dir.name, 'config.json')
        # 初始化配置管理器，使用临时路径
        self.config_manager = ConfigManager(self.temp_config_path)
    
    def tearDown(self):
        """每个测试后的清理"""
        # 清理临时目录
        self.temp_dir.cleanup()
    
    def test_load_default_config(self):
        """测试加载默认配置（配置文件不存在时）"""
        # 确保测试前配置文件不存在
        if os.path.exists(self.temp_config_path):
            os.remove(self.temp_config_path)
        
        # 加载配置
        config = self.config_manager.load_config()
        
        # 验证返回的是默认配置
        self.assertEqual(config, self.config_manager.default_config)
    
    @patch('PyQt5.QtWidgets.QMessageBox.warning')
    def test_load_invalid_config(self, mock_warning):
        """测试加载格式错误的配置文件"""
        # 创建一个格式错误的配置文件
        with open(self.temp_config_path, 'w', encoding='utf-8') as f:
            f.write('这不是有效的JSON格式')
        
        # 加载配置
        config = self.config_manager.load_config()
        
        # 验证返回的是默认配置
        self.assertEqual(config, self.config_manager.default_config)
        # 验证显示了警告消息
        mock_warning.assert_called_once()
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        # 创建自定义配置
        custom_config = self.config_manager.default_config.copy()
        custom_config['window_width'] = 1200
        custom_config['window_height'] = 800
        custom_config['show_notifications'] = False
        
        # 保存配置
        success = self.config_manager.save_config(custom_config)
        
        # 验证保存成功
        self.assertTrue(success)
        
        # 重新加载配置
        loaded_config = self.config_manager.load_config()
        
        # 验证加载的配置与保存的配置一致
        self.assertEqual(loaded_config, custom_config)
    
    def test_config_override(self):
        """测试用户配置覆盖默认配置的逻辑"""
        # 创建只有部分配置项的用户配置
        partial_config = {
            "window_width": 1400,
            "show_notifications": False
        }
        
        # 保存部分配置
        with open(self.temp_config_path, 'w', encoding='utf-8') as f:
            json.dump(partial_config, f, ensure_ascii=False, indent=2)
        
        # 加载配置
        config = self.config_manager.load_config()
        
        # 验证部分配置项被正确覆盖
        self.assertEqual(config['window_width'], 1400)
        self.assertEqual(config['show_notifications'], False)
        # 验证未指定的配置项保持默认值
        self.assertEqual(config['window_height'], self.config_manager.default_config['window_height'])
        self.assertEqual(config['notification_cooldown'], self.config_manager.default_config['notification_cooldown'])


if __name__ == '__main__':
    unittest.main()
