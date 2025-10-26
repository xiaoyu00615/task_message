#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务统计管理器
负责处理任务数据的统计分析，包括趋势统计、类别分布、完成率等
"""

from datetime import datetime, timedelta, date
from collections import defaultdict


class StatisticsManager:
    """
    任务统计管理器类
    提供各种任务统计相关的方法
    """
    
    def __init__(self, task_handler):
        """
        初始化统计管理器
        
        Args:
            task_handler: TaskHandler实例，用于获取任务数据
        """
        self.task_handler = task_handler
    
    def get_all_tasks(self):
        """
        获取所有任务（待办、已完成、超时）
        
        Returns:
            dict: 包含所有任务类别的字典
        """
        return self.task_handler.tasks
    
    def get_completed_tasks(self):
        """
        获取所有已完成的任务
        
        Returns:
            list: 已完成任务列表
        """
        return self.task_handler.tasks.get('done', [])
    
    def get_todo_tasks(self):
        """
        获取所有待办任务
        
        Returns:
            list: 待办任务列表
        """
        return self.task_handler.tasks.get('todo', [])
    
    def get_overdue_tasks(self):
        """
        获取所有超时任务
        
        Returns:
            list: 超时任务列表
        """
        return self.task_handler.tasks.get('overdue', [])
    
    def get_total_tasks_count(self):
        """
        获取系统中的总任务数（待办+已完成+超时）
        
        Returns:
            int: 总任务数
        """
        total_count = 0
        for task_list in self.get_all_tasks().values():
            total_count += len(task_list)
        return total_count
    
    def parse_datetime(self, date_str):
        """
        解析日期时间字符串
        
        Args:
            date_str: 日期时间字符串
            
        Returns:
            datetime: 解析后的datetime对象，如果解析失败返回None
        """
        formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue
        
        return None
    
    def format_date(self, dt, period='daily'):
        """
        根据统计周期格式化日期
        
        Args:
            dt: datetime对象
            period: 统计周期 ('daily', 'weekly', 'monthly')
            
        Returns:
            str: 格式化后的日期字符串
        """
        if period == 'daily':
            return dt.strftime('%Y-%m-%d')
        elif period == 'weekly':
            # 获取本周的开始日期（周一）
            start_of_week = dt - timedelta(days=dt.weekday())
            return start_of_week.strftime('%Y-%m-%d')
        elif period == 'monthly':
            return dt.strftime('%Y-%m')
        return dt.strftime('%Y-%m-%d')
    
    def get_completion_trend(self, period='daily', days=30):
        """
        获取任务完成趋势
        
        Args:
            period: 统计周期 ('daily', 'weekly', 'monthly')
            days: 统计的天数范围
            
        Returns:
            tuple: (labels, values)，其中labels是时间标签列表，values是对应完成的任务数量
        """
        completed_tasks = self.get_completed_tasks()
        
        # 创建时间标签和值的映射
        trend_data = defaultdict(int)
        
        # 获取今天的日期
        today = date.today()
        start_date = today - timedelta(days=days)
        
        # 初始化日期范围内的数据
        current_date = start_date
        while current_date <= today:
            if period == 'daily':
                label = current_date.strftime('%Y-%m-%d')
                current_date += timedelta(days=1)
            elif period == 'weekly':
                # 调整到本周的周一
                adjusted_date = current_date - timedelta(days=current_date.weekday())
                label = adjusted_date.strftime('%Y-%m-%d')
                current_date += timedelta(weeks=1)
            elif period == 'monthly':
                label = current_date.strftime('%Y-%m')
                # 调整到下个月
                if current_date.month == 12:
                    current_date = date(current_date.year + 1, 1, 1)
                else:
                    current_date = date(current_date.year, current_date.month + 1, 1)
            else:
                label = current_date.strftime('%Y-%m-%d')
                current_date += timedelta(days=1)
            
            trend_data[label] = 0
        
        # 统计已完成任务
        for task in completed_tasks:
            completed_time_str = task.get('done_time')  # 修改为正确的字段名
            if completed_time_str:
                completed_dt = self.parse_datetime(completed_time_str)
                if completed_dt:
                    completed_date = completed_dt.date()
                    # 只统计指定日期范围内的任务
                    if start_date <= completed_date <= today:
                        # 根据统计周期格式化完成日期
                        if period == 'daily':
                            label = self.format_date(completed_dt, 'daily')
                        elif period == 'weekly':
                            label = self.format_date(completed_dt, 'weekly')
                        elif period == 'monthly':
                            label = self.format_date(completed_dt, 'monthly')
                        
                        if label in trend_data:
                            trend_data[label] += 1
        
        # 排序并返回结果
        sorted_items = sorted(trend_data.items())
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        
        return labels, values
    
    def get_category_distribution(self, task_type=None):
        """
        获取任务类别分布
        
        Args:
            task_type: 任务类型过滤（'todo', 'done', 'overdue'或None表示全部）
            
        Returns:
            tuple: (categories, values)，其中categories是类别列表，values是对应类别的任务数量
        """
        # 获取对应类型的任务
        if task_type is None:
            # 获取所有任务
            all_tasks = []
            for task_list in self.get_all_tasks().values():
                all_tasks.extend(task_list)
        else:
            all_tasks = self.get_all_tasks().get(task_type, [])
        
        # 统计类别分布
        category_data = defaultdict(int)
        for task in all_tasks:
            category = task.get('category', '未分类')
            category_data[category] += 1
        
        # 排序并返回结果（按任务数量降序排列）
        sorted_items = sorted(category_data.items(), key=lambda x: x[1], reverse=True)
        categories = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        
        return categories, values
    
    def get_label_distribution(self, task_type=None):
        """
        获取任务标签分布
        
        Args:
            task_type: 任务类型过滤（'todo', 'done', 'overdue'或None表示全部）
            
        Returns:
            tuple: (labels, values)，其中labels是标签列表，values是对应标签的任务数量
        """
        # 获取对应类型的任务
        if task_type is None:
            # 获取所有任务
            all_tasks = []
            for task_list in self.get_all_tasks().values():
                all_tasks.extend(task_list)
        else:
            all_tasks = self.get_all_tasks().get(task_type, [])
        
        # 统计标签分布
        label_data = defaultdict(int)
        for task in all_tasks:
            labels = task.get('labels', [])
            if isinstance(labels, list):
                for label in labels:
                    label_data[label] += 1
        
        # 排序并返回结果（按任务数量降序排列）
        sorted_items = sorted(label_data.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        
        return labels, values
    
    def get_completion_rate(self, days=30):
        """
        计算任务按时完成率
        
        Args:
            days: 统计的天数范围
            
        Returns:
            tuple: (total_count, on_time_count, completion_rate)，分别是总任务数、按时完成任务数和完成率
        """
        completed_tasks = self.get_completed_tasks()
        overdue_tasks = self.get_overdue_tasks()
        
        today = date.today()
        start_date = today - timedelta(days=days)
        
        # 统计有截止日期的任务总数和按时完成的任务数
        total_count = 0  # 有截止日期的任务总数
        on_time_count = 0  # 按时完成的任务数
        
        # 统计已完成任务
        for task in completed_tasks:
            created_time_str = task.get('create_time')
            if created_time_str:
                created_dt = self.parse_datetime(created_time_str)
                if created_dt:
                    created_date = created_dt.date()
                    # 只统计指定日期范围内创建的任务
                    if start_date <= created_date <= today:
                        deadline_str = task.get('deadline')
                        if deadline_str:  # 只考虑有截止日期的任务
                            total_count += 1
                            
                            # 检查是否按时完成
                            completed_time_str = task.get('done_time')
                            if completed_time_str:
                                deadline_dt = self.parse_datetime(deadline_str)
                                completed_dt = self.parse_datetime(completed_time_str)
                                if deadline_dt and completed_dt:
                                    # 如果完成时间早于或等于截止时间，则视为按时完成
                                    if completed_dt <= deadline_dt:
                                        on_time_count += 1
        
        # 统计超时任务（这些任务都是有截止日期的）
        for task in overdue_tasks:
            created_time_str = task.get('create_time')
            if created_time_str:
                created_dt = self.parse_datetime(created_time_str)
                if created_dt:
                    created_date = created_dt.date()
                    # 只统计指定日期范围内创建的任务
                    if start_date <= created_date <= today:
                        total_count += 1  # 超时任务计入总数，但不计入按时完成数
        
        # 计算完成率
        completion_rate = (on_time_count / total_count * 100) if total_count > 0 else 0
        
        return total_count, on_time_count, completion_rate
    
    def get_average_completion_time(self, days=30):
        """
        计算平均完成任务所需时间
        
        Args:
            days: 统计的天数范围
            
        Returns:
            tuple: (total_count, avg_hours, avg_minutes)，分别是统计任务数、平均小时数和分钟数
        """
        completed_tasks = self.get_completed_tasks()
        
        today = date.today()
        start_date = today - timedelta(days=days)
        
        total_hours = 0
        count = 0
        
        for task in completed_tasks:
            created_time_str = task.get('create_time')  # 修改为正确的字段名
            completed_time_str = task.get('done_time')  # 修改为正确的字段名
            
            if created_time_str and completed_time_str:
                created_dt = self.parse_datetime(created_time_str)
                completed_dt = self.parse_datetime(completed_time_str)
                
                if created_dt and completed_dt:
                    created_date = created_dt.date()
                    # 只统计指定日期范围内创建的任务
                    if start_date <= created_date <= today:
                        # 计算完成时间差
                        time_diff = completed_dt - created_dt
                        time_diff_hours = time_diff.total_seconds() / 3600
                        
                        total_hours += time_diff_hours
                        count += 1
        
        # 计算平均完成时间
        avg_hours = 0
        avg_minutes = 0
        
        if count > 0:
            avg_hours = total_hours / count
            # 将小时转换为小时和分钟
            hours = int(avg_hours)
            minutes = int((avg_hours - hours) * 60)
            avg_hours, avg_minutes = hours, minutes
        
        return count, avg_hours, avg_minutes
