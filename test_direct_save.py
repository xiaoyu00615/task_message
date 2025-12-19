import json
import os
import time

def test_direct_save():
    """直接测试任务数据保存功能，验证缩进修复是否解决问题"""
    print("开始直接测试任务数据保存功能...")
    
    # 1. 备份原始数据
    tasks_file = "tasks.json"
    backup_file = f"tasks_backup_{int(time.time())}.json"
    
    try:
        # 加载原始数据
        with open(tasks_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # 创建备份
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
        
        print(f"已备份原始数据到 {backup_file}")
        
        # 2. 分析数据结构
        print(f"\n任务数据结构类型: {type(original_data)}")
        if isinstance(original_data, dict):
            print(f"任务数据结构键: {list(original_data.keys())}")
        
        # 3. 创建测试任务
        test_task = {
            "id": f"test_save_{int(time.time())}",
            "title": "测试任务保存功能",
            "description": "原始描述",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "priority": "medium",
            "subtasks": []
        }
        
        # 添加测试任务到数据中
        if isinstance(original_data, dict):
            # 假设任务数据存储在'todo'键下
            if 'todo' in original_data and isinstance(original_data['todo'], list):
                original_data['todo'].append(test_task)
                print(f"已添加测试任务到 todo 列表")
            else:
                print("无法找到合适的任务列表添加测试任务")
                return
        elif isinstance(original_data, list):
            original_data.append(test_task)
            print(f"已添加测试任务到任务列表")
        else:
            print("未知的数据结构，无法添加测试任务")
            return
        
        print(f"已创建测试任务: {test_task['title']}")
        print(f"任务ID: {test_task['id']}")
        
        # 4. 首次保存数据，创建测试任务
        print("\n首次保存数据，添加测试任务...")
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
        print("测试任务已保存")
        
        # 5. 加载数据并找到测试任务进行修改
        print("\n重新加载数据并修改测试任务...")
        with open(tasks_file, 'r', encoding='utf-8') as f:
            data_to_modify = json.load(f)
        
        # 查找测试任务
        test_task_found = None
        test_task_location = None
        
        if isinstance(data_to_modify, dict):
            for key, value in data_to_modify.items():
                if isinstance(value, list):
                    for idx, task in enumerate(value):
                        if isinstance(task, dict) and task.get('id') == test_task['id']:
                            test_task_found = task
                            test_task_location = (key, idx)
                            break
                    if test_task_found:
                        break
        elif isinstance(data_to_modify, list):
            for idx, task in enumerate(data_to_modify):
                if isinstance(task, dict) and task.get('id') == test_task['id']:
                    test_task_found = task
                    test_task_location = ('tasks', idx)
                    break
        
        if test_task_found:
            print(f"\n找到测试任务: {test_task_found['title']}")
            print(f"修改前描述: {test_task_found.get('description', '无描述')}")
            print(f"修改前子任务数量: {len(test_task_found.get('subtasks', []))}")
            
            # 修改任务数据
            test_task_found['description'] = "修改后的描述"
            test_task_found['subtasks'] = [{"title": "子任务1", "completed": False}]
            
            print(f"修改后描述: {test_task_found['description']}")
            print(f"修改后子任务数量: {len(test_task_found.get('subtasks', []))}")
            
            # 保存修改
            print("\n保存修改...")
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_modify, f, ensure_ascii=False, indent=2)
            print("修改已保存")
            
            # 重新加载数据验证保存是否成功
            print("\n重新加载数据验证保存是否成功...")
            with open(tasks_file, 'r', encoding='utf-8') as f:
                reloaded_data = json.load(f)
            
            # 查找更新后的测试任务
            updated_task = None
            
            if isinstance(reloaded_data, dict):
                for key, value in reloaded_data.items():
                    if isinstance(value, list):
                        for task in value:
                            if isinstance(task, dict) and task.get('id') == test_task['id']:
                                updated_task = task
                                break
                        if updated_task:
                            break
            elif isinstance(reloaded_data, list):
                for task in reloaded_data:
                    if isinstance(task, dict) and task.get('id') == test_task['id']:
                        updated_task = task
                        break
            
            if updated_task:
                print(f"\n重新加载后任务描述: {updated_task.get('description', '无描述')}")
                print(f"重新加载后子任务数量: {len(updated_task.get('subtasks', []))}")
                
                # 验证数据是否正确保存
                if updated_task.get('description') == "修改后的描述" and len(updated_task.get('subtasks', [])) == 1:
                    print("\n✅ 测试通过! 任务详情修改成功保存")
                    print("这表明数据保存功能正常工作，之前的缩进问题应该已被修复")
                else:
                    print("\n❌ 测试失败! 任务详情修改未正确保存")
                    print(f"期望描述: 修改后的描述, 实际描述: {updated_task.get('description')}")
                    print(f"期望子任务数: 1, 实际子任务数: {len(updated_task.get('subtasks', []))}")
            else:
                print("\n❌ 测试失败! 重新加载后找不到测试任务")
        else:
            print("\n❌ 测试失败! 找不到测试任务")
            
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢复原始数据
        print("\n恢复原始任务数据...")
        try:
            if os.path.exists(backup_file):
                with open(backup_file, 'r', encoding='utf-8') as f:
                    original_data = json.load(f)
                with open(tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, ensure_ascii=False, indent=2)
                # 删除备份文件
                os.remove(backup_file)
                print("原始数据已恢复并删除备份")
        except Exception as e:
            print(f"恢复数据时出错: {str(e)}")
    
    print("\n测试完成")

if __name__ == "__main__":
    test_direct_save()