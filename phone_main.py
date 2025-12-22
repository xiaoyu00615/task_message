#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock

import phone_ui
import phone_data
import phone_network

class TaskManagerApp(App):
    def __init__(self, **kwargs):
        super(TaskManagerApp, self).__init__(**kwargs)
        self.data_manager = None
        self.network_manager = None
        self.main_ui = None
        self.status_bar = None
        
    def build(self):
        """构建应用界面"""
        # 初始化数据管理器
        self.data_manager = phone_data.PhoneDataManager()
        
        # 初始化网络管理器
        self.network_manager = phone_network.PhoneNetworkManager(self.data_manager, self)
        
        # 创建主UI界面
        self.main_ui = phone_ui.PhoneTaskManagerUI(self.data_manager, self.network_manager)
        
        # 设置窗口大小（用于PC测试）
        Window.size = (360, 640)  # 模拟手机屏幕尺寸
        Window.clearcolor = (0.9, 0.9, 0.9, 1)  # 设置背景色
        
        # 启动后台同步
        self.network_manager.start_background_sync()
        
        # 每分钟检查一次同步状态
        Clock.schedule_interval(self.update_sync_status, 60)
        
        return self.main_ui
    
    def refresh_task_list(self):
        """刷新任务列表"""
        if self.main_ui:
            self.main_ui.refresh_task_list()
    
    def update_sync_status(self, dt):
        """更新同步状态"""
        if self.main_ui:
            self.main_ui.update_sync_status()
    
    def on_stop(self):
        """应用停止时的清理工作"""
        # 停止后台同步
        self.network_manager.stop_background_sync()
        
        # 保存缓存数据
        self.data_manager.save_cache()
        
        # 关闭数据库连接
        self.data_manager.close()
        
        super(TaskManagerApp, self).on_stop()
    
    def show_ip_config_popup(self):
        """显示IP配置弹窗"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # IP输入框
        ip_input = TextInput(
            text=self.network_manager.pc_ip if self.network_manager.pc_ip else "",
            hint_text="输入PC端IP地址",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        
        # 端口输入框
        port_input = TextInput(
            text=str(self.network_manager.pc_port),
            hint_text="输入端口号",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        
        # 扫描按钮
        scan_button = Button(
            text="扫描局域网PC",
            size_hint_y=None,
            height=40
        )
        
        # 确定按钮
        confirm_button = Button(
            text="确定",
            size_hint_y=None,
            height=40
        )
        
        # 添加控件到布局
        layout.add_widget(Label(text="PC端连接设置", size_hint_y=None, height=30))
        layout.add_widget(ip_input)
        layout.add_widget(port_input)
        layout.add_widget(scan_button)
        layout.add_widget(confirm_button)
        
        # 创建弹窗
        popup = Popup(
            title="连接设置",
            content=layout,
            size_hint=(0.9, 0.7),
            auto_dismiss=False
        )
        
        def on_scan_button_press(instance):
            """扫描局域网PC"""
            scan_button.disabled = True
            scan_button.text = "正在扫描..."
            
            def scan_network(dt):
                """执行网络扫描"""
                pcs = self.network_manager.scan_network_for_pc()
                
                if pcs:
                    ip_input.text = pcs[0]  # 默认选择第一个找到的PC
                else:
                    # 显示扫描结果弹窗
                    result_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
                    result_layout.add_widget(Label(text="未找到PC端服务器", size_hint_y=None, height=30))
                    result_button = Button(text="确定", size_hint_y=None, height=40)
                    result_layout.add_widget(result_button)
                    
                    result_popup = Popup(
                        title="扫描结果",
                        content=result_layout,
                        size_hint=(0.8, 0.4)
                    )
                    
                    result_button.bind(on_press=lambda x: result_popup.dismiss())
                    result_popup.open()
                
                scan_button.disabled = False
                scan_button.text = "扫描局域网PC"
            
            # 延迟执行扫描操作，避免UI卡顿
            Clock.schedule_once(scan_network, 0.1)
        
        def on_confirm_button_press(instance):
            """确认IP和端口设置"""
            pc_ip = ip_input.text.strip()
            pc_port = port_input.text.strip()
            
            if pc_ip and pc_port:
                try:
                    pc_port = int(pc_port)
                    self.network_manager.set_pc_address(pc_ip, pc_port)
                    
                    # 测试连接
                    if self.network_manager.test_connection(pc_ip, pc_port):
                        self.main_ui.update_sync_status()
                        popup.dismiss()
                        
                        # 立即同步数据
                        def sync_data(dt):
                            self.network_manager.sync_data()
                            self.refresh_task_list()
                        
                        Clock.schedule_once(sync_data, 0.1)
                    else:
                        # 显示连接失败弹窗
                        error_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
                        error_layout.add_widget(Label(text="连接失败，请检查IP和端口是否正确", size_hint_y=None, height=30))
                        error_button = Button(text="确定", size_hint_y=None, height=40)
                        error_layout.add_widget(error_button)
                        
                        error_popup = Popup(
                            title="连接错误",
                            content=error_layout,
                            size_hint=(0.8, 0.4)
                        )
                        
                        error_button.bind(on_press=lambda x: error_popup.dismiss())
                        error_popup.open()
                        
                except ValueError:
                    # 端口不是数字
                    error_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
                    error_layout.add_widget(Label(text="端口号必须是数字", size_hint_y=None, height=30))
                    error_button = Button(text="确定", size_hint_y=None, height=40)
                    error_layout.add_widget(error_button)
                    
                    error_popup = Popup(
                        title="输入错误",
                        content=error_layout,
                        size_hint=(0.8, 0.4)
                    )
                    
                    error_button.bind(on_press=lambda x: error_popup.dismiss())
                    error_popup.open()
        
        # 绑定按钮事件
        scan_button.bind(on_press=on_scan_button_press)
        confirm_button.bind(on_press=on_confirm_button_press)
        
        popup.open()

if __name__ == "__main__":
    # 启动应用
    TaskManagerApp().run()
