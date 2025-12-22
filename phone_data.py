import sqlite3
import json
import os
from datetime import datetime

class PhoneDataManager:
    def __init__(self, db_path='phone_tasks.db', cache_path='phone_cache.json'):
        self.db_path = db_path
        self.cache_path = cache_path
        self.conn = None
        self.cursor = None
        self.init_db()
        self.load_cache()
    
    def init_db(self):
        """初始化手机端数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建与PC端相同结构的任务表
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
        
        # 创建同步状态表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_status (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        self.conn.commit()
    
    def load_cache(self):
        """加载缓存数据"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"加载缓存失败: {e}")
                self.cache = {}
        else:
            self.cache = {}
    
    def save_cache(self):
        """保存缓存数据"""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存缓存失败: {e}")
            return False
    
    def get_sync_time(self):
        """获取最后同步时间"""
        self.cursor.execute('SELECT value FROM sync_status WHERE key=?', ('last_sync_time',))
        result = self.cursor.fetchone()
        return result[0] if result else '1970-01-01 00:00:00'
    
    def set_sync_time(self, time_str):
        """设置最后同步时间"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO sync_status (key, value)
            VALUES (?, ?)
        ''', ('last_sync_time', time_str))
        self.conn.commit()
    
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
    
    def mark_task_overdue(self, task_id):
        """标记任务为超时"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute('''
            UPDATE tasks 
            SET status='overdue', last_modified=?
            WHERE id=?
        ''', (now, task_id))
        
        self.conn.commit()
        return self.cursor.rowcount > 0
    
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
    
    def cache_tasks(self, tasks):
        """缓存任务数据"""
        self.cache['tasks'] = tasks
        self.save_cache()
    
    def get_cached_tasks(self):
        """获取缓存的任务数据"""
        return self.cache.get('tasks', {})
    
    def import_pc_data(self, pc_tasks):
        """导入PC端数据"""
        if not isinstance(pc_tasks, list):
            return False
        
        try:
            for task in pc_tasks:
                if isinstance(task, dict):
                    # 检查任务是否已存在
                    self.cursor.execute('SELECT id FROM tasks WHERE create_time=? AND name=?', 
                                      (task.get('create_time'), task.get('name')))
                    existing_task = self.cursor.fetchone()
                    
                    if existing_task:
                        # 更新现有任务
                        self.update_task(existing_task[0], task)
                    else:
                        # 插入新任务
                        self.insert_task(task, task.get('status', 'todo'))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"导入PC数据失败: {e}")
            return False
    
    def export_phone_data(self, last_sync_time):
        """导出手机端修改的数据，用于同步到PC端"""
        return self.get_tasks_after_time(last_sync_time)
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()