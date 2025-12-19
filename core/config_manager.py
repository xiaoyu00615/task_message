import os
from .json_utils import read_json_file, write_json_file

class ConfigManager:
    """负责程序配置的加载和保存"""
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.default_config = {
            "window_width": 1600,
            "window_height": 800,
            "show_notifications": True,  # 是否显示提示信息
            "notification_cooldown": 5,  # 相同通知冷却时间（分钟）
            "update_interval": 300,  # 数据更新时间间隔（秒），默认5分钟(300秒)
            "categories": ["工作", "学习", "生活", "其他"],  # 默认任务类别
            "tags": ["重要", "紧急", "常规", "计划"],  # 默认标签列表
            "auto_backup_enabled": False,  # 默认禁用自动备份
            "backup_interval": 60,  # 默认备份间隔（分钟）
            "backup_path": os.path.join(os.getcwd(), 'backups')  # 默认备份路径
        }

    def load_config(self):
        """加载配置 - 确保用户配置优先于默认配置"""
        config = read_json_file(self.config_path, None)
        
        if config is not None:
            try:
                # 关键修复：使用用户配置覆盖默认配置
                # 创建默认配置的副本，然后用用户配置项覆盖
                final_config = self.default_config.copy()
                # 逐个复制用户配置项，确保完全覆盖默认值
                for key, value in config.items():
                    final_config[key] = value
                
                print(f"[ConfigManager] 加载配置成功: backup_interval={final_config.get('backup_interval', 60)}")
                return final_config
            except Exception as e:
                print(f"[ConfigManager] 加载配置失败: {e}")
                return self.default_config
        print("[ConfigManager] 使用默认配置")
        return self.default_config

    def save_config(self, config):
        """保存配置"""
        return write_json_file(self.config_path, config)