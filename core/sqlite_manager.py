import sqlite3
import json
import os
from datetime import datetime

class SQLiteManager:
    def __init__(self, db_path='tasks.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建任务表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                deadline TEXT,
                create_time TEXT NOT NULL,
                last_modified TEXT NOT NULL,
                done_time TEXT,
                status TEXT NOT NULL, -- todo, done, overdue
                priority INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0 -- 0: 未完成, 1: 已完成
            )
        ''')
        
        self.conn.commit()
    
    def json_to_sqlite(self, json_data):
        """将JSON数据迁移到SQLite"""
        if not isinstance(json_data, dict):
            return False
        
        try:
            # 清空现有数据
            self.cursor.execute('DELETE FROM tasks')
            
            # 插入数据
            for status, tasks in json_data.items():
                for task in tasks:
                    if isinstance(task, dict):
                        self.insert_task(task, status)
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"JSON to SQLite迁移失败: {e}")
            return False
    
    def sqlite_to_json(self):
        """将SQLite数据导出到JSON"""
        self.cursor.execute('SELECT * FROM tasks')
        rows = self.cursor.fetchall()
        
        json_data = {
            'todo': [],
            'done': [],
            'overdue': []
        }
        
        for row in rows:
            task = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'deadline': row[3],
                'create_time': row[4],
                'last_modified': row[5],
                'done_time': row[6],
                'priority': row[8]
            }
            
            status = row[7]
            if status in json_data:
                json_data[status].append(task)
        
        return json_data
    
    def insert_task(self, task_info, status='todo'):
        """插入新任务"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute('''
            INSERT INTO tasks (name, description, deadline, create_time, last_modified, done_time, status, priority, completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_info.get('name', ''),
            task_info.get('description', ''),
            task_info.get('deadline', ''),
            task_info.get('create_time', now),
            now,
            None,
            status,
            task_info.get('priority', 0),
            0
        ))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def update_task(self, task_id, task_info):
        """更新任务"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute('''
            UPDATE tasks 
            SET name=?, description=?, deadline=?, last_modified=?, status=?, priority=?
            WHERE id=?
        ''', (
            task_info.get('name', ''),
            task_info.get('description', ''),
            task_info.get('deadline', ''),
            now,
            task_info.get('status', 'todo'),
            task_info.get('priority', 0),
            task_id
        ))
        
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def delete_task(self, task_id):
        """删除任务"""
        self.cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def mark_task_done(self, task_id):
        """标记任务为完成"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute('''
            UPDATE tasks 
            SET status='done', done_time=?, completed=1, last_modified=?
            WHERE id=?
        ''', (now, now, task_id))
        
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_tasks_by_status(self, status):
        """获取指定状态的任务"""
        self.cursor.execute('SELECT * FROM tasks WHERE status=? ORDER BY create_time DESC', (status,))
        rows = self.cursor.fetchall()
        
        tasks = []
        for row in rows:
            tasks.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'deadline': row[3],
                'create_time': row[4],
                'last_modified': row[5],
                'done_time': row[6],
                'priority': row[8]
            })
        
        return tasks
    
    def get_all_tasks(self):
        """获取所有任务"""
        self.cursor.execute('SELECT * FROM tasks ORDER BY create_time DESC')
        rows = self.cursor.fetchall()
        
        tasks = []
        for row in rows:
            tasks.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'deadline': row[3],
                'create_time': row[4],
                'last_modified': row[5],
                'done_time': row[6],
                'status': row[7],
                'priority': row[8]
            })
        
        return tasks
    
    def get_tasks_after_time(self, time_str):
        """获取指定时间之后修改的任务，用于增量同步"""
        self.cursor.execute('SELECT * FROM tasks WHERE last_modified > ? ORDER BY create_time DESC', (time_str,))
        rows = self.cursor.fetchall()
        
        tasks = []
        for row in rows:
            tasks.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'deadline': row[3],
                'create_time': row[4],
                'last_modified': row[5],
                'done_time': row[6],
                'status': row[7],
                'priority': row[8]
            })
        
        return tasks
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()