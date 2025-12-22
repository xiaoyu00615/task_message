from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from datetime import datetime
from kivy.lang import Builder

# 定义任务项模板
Builder.load_string('''
<TaskItemBoxLayout>
    orientation: 'horizontal'
    size_hint_y: None
    height: '60dp'
    padding: '5dp'
    spacing: '10dp'
    
    CheckBox:
        id: checkbox
        active: root.is_completed
        size_hint_x: 0.1
    
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.7
        spacing: '2dp'
        
        Label:
            text: root.task_name
            font_size: '16sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            shorten: True
        
        Label:
            text: root.task_time
            font_size: '12sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            color: 0.5, 0.5, 0.5, 1
    
    Button:
        id: delete_btn
        text: '删除'
        size_hint_x: 0.2
        background_color: 1, 0, 0, 1
        font_size: '12sp'
''')

class TaskItemBoxLayout(BoxLayout):
    """任务项布局"""
    task_name = StringProperty()
    task_time = StringProperty()
    is_completed = False
    task_data = ObjectProperty()

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    """可选择的回收视图布局"""
    touch_multiselect = False
    toggle_selection_on_touch = False

class TaskRecycleView(RecycleView):
    """任务回收视图"""
    selected_task = ObjectProperty(None)

class PhoneTaskManagerUI(BoxLayout):
    """手机端任务管理器UI"""
    sync_status = StringProperty("未连接")
    selected_tab = StringProperty("todo")
    task_list = ListProperty([])
    
    def __init__(self, data_manager, network_manager, **kwargs):
        super(PhoneTaskManagerUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.data_manager = data_manager
        self.network_manager = network_manager
        
        # 创建UI组件
        self.create_ui_components()
        
        # 加载任务数据
        self.refresh_task_list()
        
        # 更新同步状态
        self.update_sync_status()
    
    def create_ui_components(self):
        """创建UI组件"""
        # 头部区域
        header = BoxLayout(orientation='vertical', size_hint_y=0.2, padding=10)
        
        # 标题
        title = Label(
            text="任务管理器", 
            font_size='24sp', 
            bold=True,
            size_hint_y=0.4
        )
        header.add_widget(title)
        
        # 任务输入区域
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=0.6, spacing=10)
        
        self.task_input = TextInput(
            hint_text="输入新任务...",
            multiline=False,
            font_size='16sp'
        )
        
        add_btn = Button(
            text="添加",
            background_color=(0.2, 0.7, 0.3, 1),
            font_size='16sp'
        )
        add_btn.bind(on_press=self.add_task)
        
        input_layout.add_widget(self.task_input)
        input_layout.add_widget(add_btn)
        
        header.add_widget(input_layout)
        
        self.add_widget(header)
        
        # 标签页区域
        tab_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        
        self.todo_tab = Button(text="待办", font_size='14sp')
        self.todo_tab.bind(on_press=lambda x: self.switch_tab("todo"))
        
        self.done_tab = Button(text="完成", font_size='14sp')
        self.done_tab.bind(on_press=lambda x: self.switch_tab("done"))
        
        self.overdue_tab = Button(text="过期", font_size='14sp')
        self.overdue_tab.bind(on_press=lambda x: self.switch_tab("overdue"))
        
        tab_layout.add_widget(self.todo_tab)
        tab_layout.add_widget(self.done_tab)
        tab_layout.add_widget(self.overdue_tab)
        
        self.add_widget(tab_layout)
        
        # 任务列表区域 - 修复RecycleView实现
        self.task_rv = RecycleView(size_hint_y=0.6)
        self.task_rv.viewclass = 'TaskItemBoxLayout'
        self.task_rv.layout = SelectableRecycleBoxLayout(
            default_size=(None, 60),
            default_size_hint=(1, None),
            size_hint_y=None,
            orientation='vertical',
            spacing=5
        )
        self.task_rv.add_widget(self.task_rv.layout)
        
        self.add_widget(self.task_rv)
        
        # 底部区域
        footer = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10, padding=10)
        
        sync_btn = Button(
            text="同步",
            background_color=(0.3, 0.6, 0.9, 1),
            font_size='14sp'
        )
        sync_btn.bind(on_press=self.sync_data)
        
        self.sync_status_label = Label(
            text=self.sync_status,
            font_size='14sp',
            halign='center'
        )
        
        settings_btn = Button(
            text="设置",
            background_color=(0.8, 0.8, 0.8, 1),
            font_size='14sp'
        )
        settings_btn.bind(on_press=self.open_settings)
        
        footer.add_widget(sync_btn)
        footer.add_widget(self.sync_status_label)
        footer.add_widget(settings_btn)
        
        self.add_widget(footer)
    
    def switch_tab(self, tab_name):
        """切换标签页"""
        self.selected_tab = tab_name
        
        # 更新标签页样式
        tabs = [self.todo_tab, self.done_tab, self.overdue_tab]
        for tab in tabs:
            tab.background_color = (0.8, 0.8, 0.8, 1) if tab.text.lower() != tab_name else (0.3, 0.6, 0.9, 1)
        
        # 刷新任务列表
        self.refresh_task_list()
    
    def add_task(self, instance):
        """添加新任务"""
        task_name = self.task_input.text.strip()
        
        if task_name:
            # 创建任务信息
            task_info = {
                'name': task_name,
                'description': '',
                'deadline': '',
                'create_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'last_modified': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'done_time': None,
                'priority': 0
            }
            
            # 插入任务到数据库
            task_id = self.data_manager.insert_task(task_info)
            
            if task_id:
                # 清空输入框
                self.task_input.text = ''
                
                # 刷新任务列表
                self.refresh_task_list()
    
    def refresh_task_list(self):
        """刷新任务列表"""
        # 根据当前标签页获取任务
        if self.selected_tab == 'todo':
            tasks = self.data_manager.get_tasks_by_status('todo')
        elif self.selected_tab == 'done':
            tasks = self.data_manager.get_tasks_by_status('done')
        else:  # overdue
            tasks = self.data_manager.get_tasks_by_status('overdue')
        
        # 转换为RecyclerView需要的格式
        self.task_list = []
        for task in tasks:
            task_time = task.get('create_time', '')
            if task_time:
                try:
                    dt = datetime.strptime(task_time, "%Y-%m-%d %H:%M:%S")
                    task_time = dt.strftime("%m-%d %H:%M")
                except:
                    pass
            
            self.task_list.append({
                'task_name': task.get('name', ''),
                'task_time': task_time,
                'is_completed': self.selected_tab == 'done',
                'task_data': task
            })
        
        self.task_rv.data = self.task_list
    
    def sync_data(self, instance):
        """手动同步数据"""
        if self.network_manager.pc_ip:
            success = self.network_manager.sync_data()
            if success:
                self.refresh_task_list()
                self.show_info_popup("同步成功", "数据已成功同步")
            else:
                self.show_info_popup("同步失败", "请检查PC端连接")
        else:
            self.open_settings()
    
    def update_sync_status(self):
        """更新同步状态"""
        if self.network_manager.is_connected:
            self.sync_status = "已连接"
            self.sync_status_label.color = (0, 1, 0, 1)
        else:
            self.sync_status = "未连接"
            self.sync_status_label.color = (1, 0, 0, 1)
        
        self.sync_status_label.text = self.sync_status
    
    def open_settings(self, instance=None):
        """打开设置界面"""
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
            
            def scan_network():
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
            
            # 延迟执行扫描操作
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: scan_network(), 0.1)
        
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
                        self.update_sync_status()
                        popup.dismiss()
                        
                        # 立即同步数据
                        from kivy.clock import Clock
                        Clock.schedule_once(lambda dt: self.sync_data(None), 0.1)
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
    
    def show_info_popup(self, title, message):
        """显示信息弹窗"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text=message, size_hint_y=None, height=50))
        
        close_button = Button(text="确定", size_hint_y=None, height=40)
        layout.add_widget(close_button)
        
        popup = Popup(title=title, content=layout, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()