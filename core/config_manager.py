import json
import os
from PyQt5.QtWidgets import QMessageBox

class ConfigManager:
    """负责程序配置的加载和保存"""
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.default_config = {
            "window_width": 1000,
            "window_height": 700,
            "show_notifications": True,  # 是否显示提示信息
            "update_interval": 300  # 数据更新时间间隔（秒），默认5分钟(300秒)
        }

    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # 合并默认配置（防止配置项缺失）
                    return {**self.default_config,** config}
            except Exception as e:
                QMessageBox.warning(None, "配置错误", f"加载配置失败，使用默认设置: {str(e)}")
        return self.default_config

    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(None, "配置错误", f"保存配置失败: {str(e)}")
            return False