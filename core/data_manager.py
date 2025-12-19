import os
from .json_utils import read_json_file, write_json_file

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
        return read_json_file(self.file_path, self.default_data)

    def save_tasks(self, tasks):
        """保存任务数据到文件"""
        return write_json_file(self.file_path, tasks)