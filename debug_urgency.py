#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试脚本：验证任务紧急度计算逻辑
"""

import json
from datetime import datetime, timedelta
import sys

sys.path.insert(0, '.')
from core.task_handler import TaskHandler
from core.data_manager import DataManager


def test_urgency_calculation():
    """测试紧急度计算逻辑"""
    print("===== 测试紧急度计算逻辑 =====\n")
    
    # 创建一个临时测试任务
    now = datetime.now()
    
    # 创建不同剩余时间的测试任务
    test_tasks = [
        {"name": "测试任务 - 8天", "deadline": (now + timedelta(days=8)).strftime("%Y-%m-%d %H:%M"), "importance": 3, "urgency": 5},
        {"name": "测试任务 - 5天", "deadline": (now + timedelta(days=5)).strftime("%Y-%m-%d %H:%M"), "importance": 3, "urgency": 5},
        {"name": "测试任务 - 2天", "deadline": (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), "importance": 3, "urgency": 5},
        {"name": "测试任务 - 12小时", "deadline": (now + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"), "importance": 3, "urgency": 5},
        {"name": "测试任务 - 6小时", "deadline": (now + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"), "importance": 3, "urgency": 5},
    ]
    
    # 保存原始任务文件
    try:
        with open('tasks.json', 'r', encoding='utf-8') as f:
            original_tasks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        original_tasks = None
    
    # 创建临时测试数据
    test_data = {"todo": test_tasks, "overdue": [], "done": []}
    with open('tasks.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    try:
        # 初始化任务处理器
        data_manager = DataManager()
        task_handler = TaskHandler(data_manager)
        
        # 手动调用紧急度提升方法
        print("运行紧急度自动提升...")
        promoted_tasks = task_handler.auto_promote_urgency()
        
        # 重新加载任务查看结果
        tasks = data_manager.load_tasks()
        
        # 显示测试结果
        print("\n测试结果：")
        print("-" * 60)
        print(f"{'任务名称':<15} {'截止时间':<20} {'计算后紧急度':<10} {'应该紧急度':<10}")
        print("-" * 60)
        
        # 计算每个任务应该的紧急度
        for task in tasks['todo']:
            deadline_datetime = datetime.strptime(task['deadline'], "%Y-%m-%d %H:%M")
            time_remaining = deadline_datetime - now
            days_remaining = time_remaining.total_seconds() / (24 * 3600)
            
            # 计算应该的紧急度
            should_urgency = 1
            if days_remaining > 7:
                should_urgency = 5
            elif days_remaining > 3:
                should_urgency = 4
            elif days_remaining > 1:
                should_urgency = 3
            elif days_remaining > 0:
                should_urgency = 2
            
            # 显示详细信息
            print(f"{task['name']:<15} {task['deadline']:<20} {task['urgency']:<10} {should_urgency:<10}")
            print(f"      剩余天数: {days_remaining:.2f} 天")
            
            # 打印调试信息
            print(f"      计算逻辑: {days_remaining} > 7? {days_remaining > 7}")
            print(f"      计算逻辑: {days_remaining} > 3? {days_remaining > 3}")
            print(f"      计算逻辑: {days_remaining} > 1? {days_remaining > 1}")
            print(f"      计算逻辑: {days_remaining} > 0? {days_remaining > 0}")
        
        print("-" * 60)
        print(f"\n被提升的任务数: {len(promoted_tasks)}")
        
    finally:
        # 恢复原始任务文件
        if original_tasks:
            with open('tasks.json', 'w', encoding='utf-8') as f:
                json.dump(original_tasks, f, ensure_ascii=False, indent=2)
            print("\n已恢复原始任务数据")
        else:
            # 如果没有原始数据，删除测试文件
            import os
            if os.path.exists('tasks.json'):
                os.remove('tasks.json')
            print("\n已清理测试数据")


def debug_existing_tasks():
    """调试现有任务的紧急度计算"""
    print("\n===== 调试现有任务的紧急度计算 =====\n")
    
    try:
        # 加载当前任务文件
        with open('tasks.json', 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        
        # 分析每个任务
        now = datetime.now()
        print("任务分析结果：")
        print("-" * 70)
        print(f"{'序号':<5} {'任务名称':<15} {'截止时间':<20} {'当前紧急度':<10} {'应该紧急度':<10}")
        print("-" * 70)
        
        for i, task in enumerate(tasks['todo']):
            if task['deadline'] != '无截止日期':
                try:
                    # 解析截止日期
                    if ' ' in task['deadline']:
                        deadline_datetime = datetime.strptime(task['deadline'], "%Y-%m-%d %H:%M")
                    else:
                        deadline_datetime = datetime.strptime(task['deadline'], "%Y-%m-%d")
                    
                    # 计算剩余时间
                    time_remaining = deadline_datetime - now
                    days_remaining = time_remaining.total_seconds() / (24 * 3600)
                    
                    # 计算应该的紧急度
                    should_urgency = 1
                    if days_remaining > 7:
                        should_urgency = 5
                    elif days_remaining > 3:
                        should_urgency = 4
                    elif days_remaining > 1:
                        should_urgency = 3
                    elif days_remaining > 0:
                        should_urgency = 2
                    
                    # 显示信息
                    print(f"{i+1:<5} {task['name'][:12]+'...':<15} {task['deadline']:<20} {task['urgency']:<10} {should_urgency:<10}")
                    print(f"      剩余天数: {days_remaining:.2f} 天")
                    
                    # 如果有差异，标记出来
                    if task['urgency'] != should_urgency and should_urgency < task['urgency']:
                        print(f"      ⚠️ 需要升级但未升级")
                    
                except Exception as e:
                    print(f"{i+1:<5} {task['name'][:12]+'...':<15} {task['deadline']:<20} {task['urgency']:<10} {'解析错误':<10}")
                    print(f"      错误: {str(e)}")
        
        print("-" * 70)
        
    except Exception as e:
        print(f"加载任务文件时出错: {str(e)}")


def main():
    """主函数"""
    # 运行测试
    test_urgency_calculation()
    # 调试现有任务
    debug_existing_tasks()


if __name__ == "__main__":
    main()
