from flask import Flask, request, jsonify
import threading
import time
import os
from datetime import datetime
from core.data_manager import DataManager

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 初始化数据管理器
data_manager = DataManager()

# 服务器状态
server_status = {
    "running": False,
    "last_sync": None,
    "connected_clients": 0
}

# 客户端连接管理
clients = set()

@app.route('/api/ping', methods=['GET'])
def ping():
    """响应客户端的连接测试请求"""
    return jsonify({"status": "ok", "message": "PC Server is running"}), 200

@app.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有任务"""
    tasks = data_manager.load_tasks()
    return jsonify({"status": "ok", "tasks": tasks}), 200

@app.route('/api/tasks/updates', methods=['GET'])
def get_task_updates():
    """获取增量更新的任务"""
    last_sync_time = request.args.get('last_sync_time', '1970-01-01 00:00:00')
    
    try:
        # 获取指定时间之后修改的任务
        updated_tasks = data_manager.get_tasks_after_time(last_sync_time)
        return jsonify({"status": "ok", "tasks": updated_tasks}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tasks/sync', methods=['POST'])
def sync_tasks():
    """同步手机端的任务到PC端"""
    try:
        # 解析请求数据
        data = request.get_json()
        phone_tasks = data.get('tasks', [])
        
        if not isinstance(phone_tasks, list):
            return jsonify({"status": "error", "message": "Invalid data format"}), 400
        
        # 导入手机端数据
        if data_manager.import_phone_data(phone_tasks):
            # 更新最后同步时间
            server_status['last_sync'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return jsonify({"status": "ok", "message": "Tasks synchronized successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to sync tasks"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    """从手机端添加任务"""
    try:
        task_data = request.get_json()
        
        if not isinstance(task_data, dict):
            return jsonify({"status": "error", "message": "Invalid task data"}), 400
        
        # 添加任务
        task_id = data_manager.insert_task(task_data)
        
        if task_id:
            return jsonify({"status": "ok", "task_id": task_id}), 201
        else:
            return jsonify({"status": "error", "message": "Failed to add task"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/tasks/delete/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """从手机端删除任务"""
    try:
        if data_manager.delete_task(task_id):
            return jsonify({"status": "ok", "message": "Task deleted successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Task not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/server/status', methods=['GET'])
def get_server_status():
    """获取服务器状态"""
    return jsonify({"status": "ok", "server_info": server_status}), 200

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """获取连接的客户端列表"""
    return jsonify({"status": "ok", "clients": list(clients)}), 200

def run_server(host='0.0.0.0', port=5000):
    """启动Flask服务器"""
    app.run(host=host, port=port, debug=False)

class PCServer:
    def __init__(self):
        self.server_thread = None
        self.host = '0.0.0.0'
        self.port = 5000
        self.is_running = False
    
    def start(self):
        """启动服务器"""
        if not self.is_running:
            self.is_running = True
            server_status['running'] = True
            
            # 在新线程中启动Flask服务器
            self.server_thread = threading.Thread(target=run_server, args=(self.host, self.port), daemon=True)
            self.server_thread.start()
            
            print(f"PC Server started on {self.host}:{self.port}")
            return True
        return False
    
    def stop(self):
        """停止服务器"""
        if self.is_running:
            self.is_running = False
            server_status['running'] = False
            
            # Flask服务器需要通过其他方式停止，这里只是标记状态
            print("PC Server stopped")
            return True
        return False
    
    def get_status(self):
        """获取服务器状态"""
        return {
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "server_status": server_status
        }

# 启动服务器（如果作为独立程序运行）
if __name__ == '__main__':
    server = PCServer()
    server.start()
    
    # 保持程序运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("Server stopped by user")
