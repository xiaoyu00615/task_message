import requests
import json
import threading
import time
import socket
from kivy.logger import Logger

class PhoneNetworkManager:
    def __init__(self, data_manager, ui_app=None):
        self.data_manager = data_manager
        self.ui_app = ui_app
        self.pc_ip = None
        self.pc_port = 5000
        self.is_connected = False
        self.sync_thread = None
        self.sync_interval = 30  # 同步间隔（秒）
    
    def set_pc_address(self, ip, port=5000):
        """设置PC端IP地址和端口"""
        self.pc_ip = ip
        self.pc_port = port
    
    def test_connection(self, ip, port=5000):
        """测试与PC端的连接"""
        try:
            url = f"http://{ip}:{port}/api/ping"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            Logger.error(f"连接测试失败: {e}")
            return False
    
    def start_background_sync(self):
        """启动后台同步线程"""
        if self.sync_thread and self.sync_thread.is_alive():
            return
        
        self.sync_thread = threading.Thread(target=self._background_sync_loop, daemon=True)
        self.sync_thread.start()
    
    def stop_background_sync(self):
        """停止后台同步线程"""
        self.is_connected = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
    
    def _background_sync_loop(self):
        """后台同步循环"""
        while True:
            if self.pc_ip:
                try:
                    self.is_connected = self.test_connection(self.pc_ip, self.pc_port)
                    if self.is_connected:
                        self.sync_data()
                except Exception as e:
                    Logger.error(f"后台同步出错: {e}")
                    self.is_connected = False
            else:
                self.is_connected = False
            
            # 等待下一次同步
            time.sleep(self.sync_interval)
    
    def sync_data(self):
        """同步数据（双向增量同步）"""
        try:
            # 获取最后同步时间
            last_sync_time = self.data_manager.get_sync_time()
            
            # 1. 从PC端获取增量更新
            pc_updates = self._get_pc_updates(last_sync_time)
            if pc_updates:
                # 导入PC端更新到手机数据库
                for task in pc_updates:
                    self.data_manager.insert_task(task, task.get('status', 'todo'))
                
                # 更新UI
                if self.ui_app:
                    self.ui_app.refresh_task_list()
            
            # 2. 向PC端发送手机端的增量更新
            phone_updates = self.data_manager.export_phone_data(last_sync_time)
            if phone_updates:
                self._send_phone_updates(phone_updates)
            
            # 3. 更新最后同步时间
            self.data_manager.set_sync_time(time.strftime("%Y-%m-%d %H:%M:%S"))
            
            return True
        except Exception as e:
            Logger.error(f"数据同步失败: {e}")
            return False
    
    def _get_pc_updates(self, last_sync_time):
        """从PC端获取增量更新"""
        try:
            url = f"http://{self.pc_ip}:{self.pc_port}/api/tasks/updates"
            params = {"last_sync_time": last_sync_time}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json().get("tasks", [])
            else:
                Logger.warning(f"从PC获取更新失败: {response.status_code}")
                return []
        except Exception as e:
            Logger.error(f"获取PC更新出错: {e}")
            return []
    
    def _send_phone_updates(self, phone_updates):
        """向PC端发送手机端的增量更新"""
        try:
            url = f"http://{self.pc_ip}:{self.pc_port}/api/tasks/sync"
            data = {"tasks": phone_updates}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                Logger.info(f"手机更新已发送到PC: {len(phone_updates)}条任务")
                return True
            else:
                Logger.warning(f"发送手机更新到PC失败: {response.status_code}")
                return False
        except Exception as e:
            Logger.error(f"发送手机更新出错: {e}")
            return False
    
    def sync_now(self):
        """立即执行同步（供用户手动触发）"""
        return self.sync_data()
    
    def get_local_ip(self):
        """获取本地IP地址"""
        try:
            # 创建一个UDP socket来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接到一个外部服务器（不需要实际连接，只是为了获取本地IP）
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            Logger.error(f"获取本地IP失败: {e}")
            return "127.0.0.1"
    
    def scan_network_for_pc(self, base_ip=None, port=5000):
        """扫描局域网寻找PC端服务器"""
        found_pcs = []
        
        try:
            if not base_ip:
                local_ip = self.get_local_ip()
                base_ip = ".".join(local_ip.split(".")[:-1]) + "."
            else:
                if not base_ip.endswith("."):
                    base_ip = "\.".join(base_ip.split(".")[:-1]) + "."
            
            # 扫描同一网段的IP（1-254）
            def scan_ip(ip):
                try:
                    if self.test_connection(ip, port):
                        found_pcs.append(ip)
                except Exception:
                    pass
            
            threads = []
            for i in range(1, 255):
                ip = f"{base_ip}{i}"
                t = threading.Thread(target=scan_ip, args=(ip,), daemon=True)
                threads.append(t)
                t.start()
            
            # 等待所有线程完成
            for t in threads:
                t.join(timeout=2)
            
            return found_pcs
        except Exception as e:
            Logger.error(f"网络扫描出错: {e}")
            return []
    
    def send_task_to_pc(self, task_data):
        """发送单个任务到PC端"""
        try:
            url = f"http://{self.pc_ip}:{self.pc_port}/api/tasks/add"
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=task_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                Logger.info("任务已发送到PC")
                return True
            else:
                Logger.warning(f"发送任务到PC失败: {response.status_code}")
                return False
        except Exception as e:
            Logger.error(f"发送任务出错: {e}")
            return False
    
    def delete_task_from_pc(self, task_id):
        """从PC端删除任务"""
        try:
            url = f"http://{self.pc_ip}:{self.pc_port}/api/tasks/delete/{task_id}"
            
            response = requests.delete(url, timeout=10)
            
            if response.status_code == 200:
                Logger.info(f"任务{task_id}已从PC删除")
                return True
            else:
                Logger.warning(f"从PC删除任务失败: {response.status_code}")
                return False
        except Exception as e:
            Logger.error(f"删除任务出错: {e}")
            return False
