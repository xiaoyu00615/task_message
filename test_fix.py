import json
import datetime
import os

# 创建测试任务并验证紧急度计算逻辑
def test_urgency_update():
    # 备份原始任务数据
    tasks_file = 'tasks.json'
    backup_file = 'tasks_backup.json'
    
    # 读取原始数据
    with open(tasks_file, 'r', encoding='utf-8') as f:
        original_tasks = json.load(f)
    
    # 备份数据
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(original_tasks, f, ensure_ascii=False, indent=2)
    
    try:
        # 创建一个新的测试任务，剩余时间在1天内
        new_task = {
            "id": "test_task_urgency",
            "title": "测试紧急度更新任务",
            "description": "测试1天内任务的紧急度更新",
            "created_at": datetime.datetime.now().isoformat(),
            "deadline": (datetime.datetime.now() + datetime.timedelta(hours=12)).isoformat(),
            "urgency": 5,  # 故意设置为最高等级
            "completed": False
        }
        
        # 添加到任务列表
        tasks = original_tasks.copy()
        tasks.append(new_task)
        
        # 保存测试数据
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        
        print(f"已创建测试任务: {new_task['title']}")
        print(f"截止时间: {new_task['deadline']}")
        print(f"初始紧急度: {new_task['urgency']}")
        print(f"预期紧急度: 2 (1天内任务)")
        print("\n请重启应用程序以测试紧急度更新逻辑")
        print("完成测试后，运行此脚本的restore选项恢复数据")
        
    except Exception as e:
        print(f"发生错误: {e}")
        # 发生错误时恢复原始数据
        if os.path.exists(backup_file):
            with open(backup_file, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(original_data, f, ensure_ascii=False, indent=2)
            print("已恢复原始任务数据")

def restore_original_data():
    tasks_file = 'tasks.json'
    backup_file = 'tasks_backup.json'
    
    if os.path.exists(backup_file):
        with open(backup_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
        print("已恢复原始任务数据")
        # 删除备份文件
        os.remove(backup_file)
    else:
        print("未找到备份文件")

if __name__ == "__main__":
    print("1. 创建测试任务")
    print("2. 恢复原始数据")
    choice = input("请选择操作 (1/2): ")
    
    if choice == "1":
        test_urgency_update()
    elif choice == "2":
        restore_original_data()
    else:
        print("无效的选择")
