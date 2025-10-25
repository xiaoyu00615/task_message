#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：用于手动触发任务紧急度升级并显示托盘通知
"""

import sys
import time
from datetime import datetime, timedelta
import json

# 添加项目根目录到路径
sys.path.insert(0, '.')


def create_test_task():
    """创建一个用于测试的紧急度5任务"""
    # 加载现有任务文件
    try:
        with open('tasks.json', 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        tasks = {"todo": [], "overdue": [], "done": []}
    
    # 创建一个紧急度5的任务，设置截止时间为1天后（应该升级为紧急度3）
    test_task = {
        "name": "测试紧急度升级任务",
        "deadline": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
        "importance": 2,
        "urgency": 5,  # 初始紧急度为5（最不紧急）
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 添加到待办任务列表
    tasks["todo"].append(test_task)
    
    # 保存任务文件
    with open('tasks.json', 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    print(f"已创建测试任务：{test_task['name']}")
    print(f"截止时间：{test_task['deadline']}")
    print(f"初始紧急度：{test_task['urgency']}")
    print("\n请运行应用程序，系统将在任务加载时自动提升紧急度并显示托盘通知")


def main():
    """主函数"""
    print("===== 任务紧急度升级测试工具 =====\n")
    print("此工具将创建一个紧急度5的任务，其截止时间会触发自动升级")
    
    # 创建测试任务
    create_test_task()
    
    # 提示用户如何测试
    print("\n测试选项:")
    print("1. 运行 'python main.py' 启动应用程序，查看托盘通知")
    print("2. 修改 tasks.json 中的截止时间为更近的时间，再次启动应用程序测试多次升级")
    print("\n按任意键退出...")
    input()


if __name__ == "__main__":
    main()
