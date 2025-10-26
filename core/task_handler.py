from datetime import datetime, date, timedelta
import time


class TaskHandler:
    """负责任务的逻辑处理（添加、标记完成、删除、检查超时等）"""

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.tasks = self.data_manager.load_tasks()
        self.check_overdue_tasks()  # 初始化时检查超时任务
        self.auto_promote_urgency()  # 初始化时自动提升紧急度
    
    def calculate_time_remaining(self, task):
        """
        计算任务剩余时间
        返回格式化的倒计时字符串，如"剩余: 2天 3小时 45分钟"或"已超时: 1小时 30分钟"
        当剩余时间为0分钟时开始显示秒数
        """
        if task["deadline"] == "无截止日期":
            return "无截止日期"
        
        try:
            # 尝试解析包含时间的格式
            try:
                deadline_datetime = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
            except ValueError:
                # 回退到旧格式（仅日期）
                deadline_datetime = datetime.strptime(task["deadline"], "%Y-%m-%d")
            
            now = datetime.now()
            time_diff = deadline_datetime - now
            total_seconds = time_diff.total_seconds()
            
            if total_seconds <= 0:
                # 已超时
                total_seconds = abs(total_seconds)
                days = int(total_seconds // (24 * 3600))
                hours = int((total_seconds % (24 * 3600)) // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                
                parts = []
                if days > 0:
                    parts.append(f"{days}天")
                if hours > 0:
                    parts.append(f"{hours}小时")
                if minutes > 0 or not parts:  # 至少显示分钟
                    parts.append(f"{minutes}分钟")
                # 当小时和天都为0时，显示秒数
                if not days and not hours:
                    parts.append(f"{seconds}秒")
                
                return f"已超时: {' '.join(parts)}"
            else:
                # 未超时
                days = int(total_seconds // (24 * 3600))
                hours = int((total_seconds % (24 * 3600)) // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                
                parts = []
                if days > 0:
                    parts.append(f"{days}天")
                if hours > 0:
                    parts.append(f"{hours}小时")
                if minutes > 0 or not parts:  # 至少显示分钟
                    parts.append(f"{minutes}分钟")
                # 当小时和天都为0时，显示秒数
                if not days and not hours:
                    parts.append(f"{seconds}秒")
                
                return f"剩余: {' '.join(parts)}"
        except Exception as e:
            return "时间格式错误"

    def add_task(self, task_info):
        """添加新任务到待办列表"""
        # 补充创建时间（精确到秒）
        task = {
            **task_info,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.tasks["todo"].append(task)
        self.data_manager.save_tasks(self.tasks)
        return task

    def mark_as_done(self, task_type, index):
        """将指定任务标记为完成"""
        if 0 <= index < len(self.tasks[task_type]):
            task = self.tasks[task_type].pop(index)
            task["done_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.tasks["done"].append(task)
            self.data_manager.save_tasks(self.tasks)
            return True
        return False
        
    def mark_task_done_by_identifier(self, task_type, create_time, task_name):
        """通过任务标识（创建时间和名称）标记任务为完成
        
        这个方法解决了定时器刷新导致索引变化的问题，通过唯一标识找到正确的任务
        """
        if task_type not in self.tasks:
            return False
            
        # 遍历任务列表，查找匹配的任务
        task_index = -1
        for i, task in enumerate(self.tasks[task_type]):
            # 优先使用创建时间和名称进行精确匹配
            if create_time and task.get('create_time') == create_time:
                if task['name'] == task_name:
                    task_index = i
                    break
            # 如果没有创建时间或不匹配，则尝试仅使用名称匹配
            elif task['name'] == task_name:
                # 只有在没有找到精确匹配时才使用名称匹配
                if task_index == -1:
                    task_index = i
        
        # 如果找到匹配的任务，则标记为完成
        if task_index != -1:
            return self.mark_as_done(task_type, task_index)
        
        return False

    def delete_task(self, task_type, index):
        """删除指定任务"""
        if 0 <= index < len(self.tasks[task_type]):
            self.tasks[task_type].pop(index)
            self.data_manager.save_tasks(self.tasks)
            return True
        return False
        
    def delete_task_by_identifier(self, task_type, create_time, task_name):
        """通过任务标识（创建时间和名称）删除任务
        
        这个方法解决了定时器刷新导致索引变化的问题，通过唯一标识找到正确的任务
        """
        if task_type not in self.tasks:
            return False
            
        # 遍历任务列表，查找匹配的任务
        task_index = -1
        for i, task in enumerate(self.tasks[task_type]):
            # 优先使用创建时间和名称进行精确匹配
            if create_time and task.get('create_time') == create_time:
                if task['name'] == task_name:
                    task_index = i
                    break
            # 如果没有创建时间或不匹配，则尝试仅使用名称匹配
            elif task['name'] == task_name:
                # 只有在没有找到精确匹配时才使用名称匹配
                if task_index == -1:
                    task_index = i
        
        # 如果找到匹配的任务，则删除
        if task_index != -1:
            return self.delete_task(task_type, task_index)
        
        return False

    def check_overdue_tasks(self):
        """检查并移动超时任务，返回新超时的任务列表"""
        print(f"[{time.strftime('%H:%M:%S')}] 正在检查超时任务...")
        today = date.today()
        overdue_indices = []
        newly_overdue_tasks = []  # 存储新超时的任务

        # 检查待办任务中的超时任务
        for i, task in enumerate(self.tasks["todo"]):
            if task["deadline"] != "无截止日期":
                try:
                    # 尝试解析包含时间的格式
                    try:
                        deadline_datetime = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                    except ValueError:
                        # 回退到旧格式（仅日期）
                        deadline_datetime = datetime.strptime(task["deadline"], "%Y-%m-%d")
                    
                    if deadline_datetime < datetime.now():
                        print(f"[{time.strftime('%H:%M:%S')}] 发现超时任务: {task['name']}, 截止时间: {task['deadline']}")
                        overdue_indices.append(i)
                        newly_overdue_tasks.append(task)
                except Exception as e:
                    print(f"[{time.strftime('%H:%M:%S')}] 解析任务日期出错: {task['name']}, 错误: {e}")
                    continue

        # 逆序移除避免索引问题
        for i in sorted(overdue_indices, reverse=True):
            task = self.tasks["todo"].pop(i)
            self.tasks["overdue"].append(task)
            print(f"[{time.strftime('%H:%M:%S')}] 已将任务 '{task['name']}' 从待办移至超时列表")

        if overdue_indices:
            print(f"[{time.strftime('%H:%M:%S')}] 共移动 {len(overdue_indices)} 个超时任务")
            self.data_manager.save_tasks(self.tasks)
            print(f"[{time.strftime('%H:%M:%S')}] 已保存更新后的任务数据")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 未发现需要移动的超时任务")
            
        return newly_overdue_tasks  # 返回新超时的任务列表

    def auto_promote_urgency(self):
        """根据截止日期自动提升任务紧急度"""
        today = date.today()
        updated = False
        promoted_tasks = []  # 记录被提升紧急度的任务

        for task in self.tasks["todo"]:
            if task["deadline"] == "无截止日期":
                continue  # 无截止日期的任务不自动提升

            try:
                # 尝试解析包含时间的格式
                try:
                    deadline_datetime = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                except ValueError:
                    # 回退到旧格式（仅日期）
                    deadline_datetime = datetime.strptime(task["deadline"], "%Y-%m-%d")
                
                # 计算剩余天数（包含小时和分钟）
                now = datetime.now()
                time_remaining = deadline_datetime - now
                days_remaining = time_remaining.total_seconds() / (24 * 3600)  # 转换为天

                # 根据剩余天数自动调整紧急度（1最紧急）
                if days_remaining > 7:
                    target_urgency = 5  # 7天以上：最不紧急
                elif days_remaining > 3:
                    target_urgency = 4  # 4-7天：较不紧急
                elif days_remaining > 1:
                    target_urgency = 3  # 2-3天：中等
                elif days_remaining > 0:
                    target_urgency = 2  # 1天内：紧急
                else:
                    target_urgency = 1  # 已过期或今天：最紧急

                # 根据剩余时间正确更新紧急度，无论提升还是降低
                if target_urgency != task["urgency"]:
                    old_urgency = task["urgency"]
                    task["urgency"] = target_urgency
                    updated = True
                    promoted_tasks.append({
                        "name": task["name"],
                        "old_urgency": old_urgency,
                        "new_urgency": target_urgency,
                        "reason": f"剩余时间：{days_remaining:.1f}天"
                    })

            except Exception as e:
                continue  # 日期格式错误的任务不处理

        if updated:
            self.data_manager.save_tasks(self.tasks)
            
        return promoted_tasks  # 返回被提升的任务列表

    def get_sorted_tasks(self, task_type):
        """获取按紧急度+星级+剩余时间智能排序的任务列表"""
        # 先检查并更新紧急度
        if task_type == "todo":
            self.auto_promote_urgency()

        # 定义排序键函数，添加剩余时间作为第三排序条件
        def get_sort_key(task):
            # 第一条件：无截止日期的任务排在最后
            has_deadline = task["deadline"] != "无截止日期"
            
            # 第二条件：紧急度（1最优先）
            urgency = task["urgency"] if has_deadline else 0
            
            # 第三条件：重要度降序（3星最优先）
            importance = -task["importance"]
            
            # 第四条件：剩余时间（对于有截止日期的任务）
            remaining_time = 0
            if has_deadline:
                try:
                    # 尝试解析包含时间的格式
                    try:
                        deadline_datetime = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                    except ValueError:
                        # 回退到旧格式（仅日期）
                        deadline_datetime = datetime.strptime(task["deadline"], "%Y-%m-%d")
                    
                    # 计算剩余时间秒数
                    now = datetime.now()
                    remaining_seconds = (deadline_datetime - now).total_seconds()
                    remaining_time = remaining_seconds
                except Exception:
                    # 日期解析错误时，给一个较大的值，让它排在后面
                    remaining_time = float('inf')
            
            # 复合排序键：无截止日期标记, 紧急度, 重要度, 剩余时间
            return (not has_deadline, urgency, importance, remaining_time)

        # 智能排序核心逻辑：
        # 1. 优先将无截止日期的任务排在最后
        # 2. 有截止日期的任务：按紧急度升序（1最优先）
        # 3. 紧急度相同时按重要度降序（3星最优先）
        # 4. 紧急度和重要度都相同时按剩余时间升序（剩余时间少的优先）
        if task_type in ["todo", "overdue"]:
            return sorted(
                self.tasks[task_type],
                key=get_sort_key
            )
        # 已完成任务按完成时间倒序
        elif task_type == "done":
            return sorted(
                self.tasks[task_type],
                key=lambda x: x["done_time"],
                reverse=True
            )
        return self.tasks[task_type]