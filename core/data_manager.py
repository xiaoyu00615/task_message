import json
import os
from PyQt5.QtWidgets import QMessageBox

class DataManager:
    """负责任务数据的加载和保存"""
    def __init__(self, file_path="tasks.json"):
        self.file_path = file_path
        self.default_data = {
            "todo": [],
            "done": [],
            "overdue": []
        }

    def load_tasks(self):
        """从文件加载任务数据"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                QMessageBox.warning(None, "错误", f"加载数据失败: {str(e)}")
        return self.default_data

    def save_tasks(self, tasks):
        """保存任务数据到文件"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(None, "错误", f"保存数据失败: {str(e)}")
            return False