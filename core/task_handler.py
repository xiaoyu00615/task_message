from datetime import datetime, date, timedelta


class TaskHandler:
    """负责任务的逻辑处理（添加、标记完成、删除、检查超时等）"""

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.tasks = self.data_manager.load_tasks()
        self.check_overdue_tasks()  # 初始化时检查超时任务
        self.auto_promote_urgency()  # 初始化时自动提升紧急度

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

    def delete_task(self, task_type, index):
        """删除指定任务"""
        if 0 <= index < len(self.tasks[task_type]):
            self.tasks[task_type].pop(index)
            self.data_manager.save_tasks(self.tasks)
            return True
        return False

    def check_overdue_tasks(self):
        """检查并移动超时任务"""
        today = date.today()
        overdue_indices = []

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
                        overdue_indices.append(i)
                except:
                    continue

        # 逆序移除避免索引问题
        for i in sorted(overdue_indices, reverse=True):
            task = self.tasks["todo"].pop(i)
            self.tasks["overdue"].append(task)

        self.data_manager.save_tasks(self.tasks)

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
        """获取按紧急度+星级智能排序的任务列表"""
        # 先检查并更新紧急度
        if task_type == "todo":
            self.auto_promote_urgency()

        # 智能排序核心逻辑：
        # 1. 优先按紧急度升序（1最优先）
        # 2. 紧急度相同时按星级降序（3星最优先）
        if task_type in ["todo", "overdue"]:
            return sorted(
                self.tasks[task_type],
                key=lambda x: (x["urgency"], -x["importance"])  # 复合排序键
            )
        # 已完成任务按完成时间倒序
        elif task_type == "done":
            return sorted(
                self.tasks[task_type],
                key=lambda x: x["done_time"],
                reverse=True
            )
        return self.tasks[task_type]