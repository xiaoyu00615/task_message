#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新测试任务的截止时间为更近的时间，用于测试多次紧急度升级
"""

import sys
import json
from datetime import datetime, timedelta


def update_test_task_deadline():
    """更新测试任务的截止时间"""
    try:
        # 加载任务文件
        with open('tasks.json', 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        
        # 查找测试任务
        test_task_found = False
        for task in tasks["todo"]:
            if task["name"] == "测试紧急度升级任务":
                # 设置新的截止时间为5小时后（应该升级到更紧急的级别）
                new_deadline = (datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M")
                task["deadline"] = new_deadline
                # 重置紧急度为5，以便再次测试升级
                task["urgency"] = 5
                test_task_found = True
                print(f"已更新测试任务截止时间为：{new_deadline}")
                print(f"已重置紧急度为：5")
                break
        
        if not test_task_found:
            print("未找到测试任务，请先运行 test_promote.py 创建测试任务")
            return False
        
        # 保存更新后的任务文件
        with open('tasks.json', 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        
        print("\n任务文件已更新！")
        print("请重启应用程序，系统将再次升级任务紧急度并显示托盘通知")
        return True
        
    except Exception as e:
        print(f"更新任务时出错：{e}")
        return False


def main():
    """主函数"""
    print("===== 更新测试任务截止时间 =====\n")
    print("此工具将更新测试任务的截止时间为更近的时间，以便测试多次紧急度升级")
    update_test_task_deadline()


if __name__ == "__main__":
    main()
