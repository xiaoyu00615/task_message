import json
import os
from PyQt5.QtWidgets import QMessageBox


def read_json_file(file_path, default_value=None):
    """
    读取JSON文件内容
    
    Args:
        file_path: JSON文件路径
        default_value: 文件不存在或读取失败时的默认值
        
    Returns:
        读取的JSON数据或默认值
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.warning(None, "错误", f"加载数据失败: {str(e)}")
    return default_value


def write_json_file(file_path, data):
    """
    将数据写入JSON文件
    
    Args:
        file_path: JSON文件路径
        data: 要写入的数据
        
    Returns:
        bool: 写入成功返回True，失败返回False
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        QMessageBox.warning(None, "错误", f"保存数据失败: {str(e)}")
        return False
