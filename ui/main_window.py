import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QGroupBox, QFormLayout, QLineEdit, QComboBox,
                             QDateTimeEdit, QPushButton, QSplitter, QMessageBox,
                             QSystemTrayIcon, QMenu, QAction, qApp, QDialog,
                             QSpinBox, QLabel, QCheckBox, QSizePolicy, QGridLayout,
                             QTabWidget)
from PyQt5.QtCore import Qt, QDate, QDateTime, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QBrush
from datetime import datetime, date, timedelta
import time
from pynput.keyboard import GlobalHotKeys
import threading

from core.data_manager import DataManager
from core.task_handler import TaskHandler
from core.config_manager import ConfigManager
from ui.widgets import TaskListWidget
from ui.statistics_widget import StatisticsWidget


class HotkeyListener(QThread):
    """快捷键监听线程"""
    trigger = pyqtSignal()  # 触发信号

    def run(self):
        """监听全局快捷键 Ctrl+Alt+T"""
        with GlobalHotKeys({
            '<ctrl>+<alt>+t': self.on_triggered
        }) as h:
            h.join()

    def on_triggered(self):
        """快捷键被触发时发送信号"""
        self.trigger.emit()


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()  # 复制当前配置
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("设置")
        self.setGeometry(200, 200, 300, 200)
        layout = QVBoxLayout(self)

        # 窗口大小设置
        size_group = QGroupBox("窗口大小设置")
        size_layout = QFormLayout()

        self.width_spin = QSpinBox()
        self.width_spin.setRange(800, 2000)  # 最小800，最大2000
        self.width_spin.setValue(self.config["window_width"])
        size_layout.addRow("窗口宽度:", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(600, 1500)  # 最小600，最大1500
        self.height_spin.setValue(self.config["window_height"])
        size_layout.addRow("窗口高度:", self.height_spin)

        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # 提示信息设置
        self.notify_check = QCheckBox("显示提示信息（系统托盘消息）")
        self.notify_check.setChecked(self.config["show_notifications"])
        layout.addWidget(self.notify_check)
        
        # 数据更新时间间隔设置
        update_group = QGroupBox("数据更新设置")
        update_layout = QFormLayout()
        
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 3600)  # 1到3600秒
        # 直接使用配置中的秒值
        self.update_interval_spin.setValue(self.config["update_interval"])
        update_layout.addRow("更新时间间隔（秒）:", self.update_interval_spin)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def accept(self):
        """确认设置"""
        self.config["window_width"] = self.width_spin.value()
        self.config["window_height"] = self.height_spin.value()
        self.config["show_notifications"] = self.notify_check.isChecked()
        # 直接保存秒值
        self.config["update_interval"] = self.update_interval_spin.value()
        super().accept()

    def get_config(self):
        """返回修改后的配置"""
        return self.config


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        # 初始化数据管理器和任务处理器
        self.data_manager = DataManager()
        self.task_handler = TaskHandler(self.data_manager)

        # 窗口设置（从配置加载）
        self.setWindowTitle("事务处理程序")
        self.setGeometry(100, 100, self.config["window_width"], self.config["window_height"])
        self.setMinimumSize(800, 600)

        # 初始化系统托盘
        self.init_system_tray()

        # 初始化快捷键监听
        self.init_hotkey_listener()

        # 初始化UI
        self.init_ui()
        self.refresh_all_lists()
        
        # 初始化定时器用于刷新倒计时显示
        self.init_timer()

        # 默认隐藏窗口（后台运行）
        self.hide()
        self.show_system_tray_message("程序已启动", "使用 Ctrl+Alt+T 呼出窗口")

    def init_system_tray(self):
        """初始化系统托盘图标和菜单"""
        self.tray_icon = QSystemTrayIcon(self)
        # 使用标准信息图标
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_MessageBoxInformation))
        self.tray_icon.setToolTip("事务处理程序")

        # 创建托盘菜单
        tray_menu = QMenu(self)

        # 显示窗口动作
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        # 设置动作
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)

        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # 点击托盘图标显示/隐藏窗口
        self.tray_icon.activated.connect(self.on_tray_activated)

    def init_hotkey_listener(self):
        """初始化快捷键监听"""
        self.hotkey_thread = HotkeyListener()
        self.hotkey_thread.trigger.connect(self.toggle_window_visibility)
        # 启动线程（守护线程，主程序退出时自动结束）
        self.hotkey_thread.daemon = True
        self.hotkey_thread.start()

    def init_ui(self):
        """初始化界面"""
        # 主部件和布局
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # 左侧：垂直布局包含输入面板和搜索筛选
        left_layout = QVBoxLayout()
        
        # 添加任务输入区域（放在顶部）
        input_panel = self.create_input_panel()
        left_layout.addWidget(input_panel)
        
        # 添加搜索和筛选面板（放在下面）
        search_filter_panel = self.create_search_filter_panel()
        left_layout.addWidget(search_filter_panel)
        
        # 创建左侧容器部件并应用布局
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget)

        # 右侧：使用标签页切换任务列表和统计界面
        self.tab_widget = QTabWidget()
        
        # 创建任务列表标签页内容
        task_list_widget = QWidget()
        task_list_layout = QHBoxLayout(task_list_widget)
        
        # 任务列表区域（使用分割器）
        splitter = QSplitter(Qt.Horizontal)

        # 待办任务列表（带数量统计）
        self.todo_list = TaskListWidget("todo")
        self.todo_list.done_btn.clicked.connect(lambda: self.handle_mark_done("todo"))
        self.todo_list.delete_btn.clicked.connect(lambda: self.handle_delete("todo"))
        self.todo_group = QGroupBox("待完成任务 (0)")  # 初始数量0
        self.todo_group.setLayout(QVBoxLayout())
        self.todo_group.layout().addWidget(self.todo_list)
        splitter.addWidget(self.todo_group)

        # 超时任务列表（带数量统计）
        self.overdue_list = TaskListWidget("overdue")
        self.overdue_list.done_btn.clicked.connect(lambda: self.handle_mark_done("overdue"))
        self.overdue_list.delete_btn.clicked.connect(lambda: self.handle_delete("overdue"))
        self.overdue_group = QGroupBox("超时任务 (0)")  # 初始数量0
        self.overdue_group.setLayout(QVBoxLayout())
        self.overdue_group.layout().addWidget(self.overdue_list)
        splitter.addWidget(self.overdue_group)

        # 已完成任务列表（带数量统计）
        self.done_list = TaskListWidget("done")
        self.done_list.delete_btn.clicked.connect(lambda: self.handle_delete("done"))
        self.done_group = QGroupBox("已完成任务 (0)")  # 初始数量0
        self.done_group.setLayout(QVBoxLayout())
        self.done_group.layout().addWidget(self.done_list)
        splitter.addWidget(self.done_group)

        # 设置分割器比例
        splitter.setSizes([300, 300, 300])
        
        # 添加分割器到任务列表标签页布局
        task_list_layout.addWidget(splitter)
        
        # 创建统计界面标签页
        self.statistics_widget = StatisticsWidget(self.task_handler)
        
        # 添加标签页
        self.tab_widget.addTab(task_list_widget, "任务列表")
        self.tab_widget.addTab(self.statistics_widget, "任务统计")
        
        # 添加标签页到主布局
        main_layout.addWidget(self.tab_widget, 1)

    def create_input_panel(self):
        """创建任务输入面板（优化紧急度选项）"""
        from PyQt5.QtWidgets import QComboBox
        panel = QGroupBox("添加新任务")
        layout = QFormLayout()

        # 任务名称
        self.task_name_input = QLineEdit()
        layout.addRow("事务名称:", self.task_name_input)

        # 截止日期时间
        self.deadline_input = QDateTimeEdit()
        self.deadline_input.setDateTime(QDateTime.currentDateTime().addDays(1))  # 默认明天同一时间
        self.deadline_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setMinimumWidth(200)  # 拉长输入框

        # 快捷截止时间按钮
        self.one_week_btn = QPushButton("一周")
        self.one_week_btn.setMinimumHeight(25)
        self.one_week_btn.clicked.connect(self.set_one_week_deadline)
        
        self.no_deadline_btn = QPushButton("无截止日期")
        self.no_deadline_btn.setCheckable(True)
        self.no_deadline_btn.setMinimumHeight(25)
        self.no_deadline_btn.clicked.connect(self.toggle_deadline)

        deadline_layout = QVBoxLayout()
        date_time_layout = QHBoxLayout()
        date_time_layout.addWidget(self.deadline_input)
        deadline_layout.addLayout(date_time_layout)
        
        quick_deadline_layout = QHBoxLayout()
        quick_deadline_layout.addWidget(self.one_week_btn)
        quick_deadline_layout.addWidget(self.no_deadline_btn)
        deadline_layout.addLayout(quick_deadline_layout)
        
        layout.addRow("截止日期:", deadline_layout)

        # 重要等级（1-3星）
        self.importance_input = QComboBox()
        self.importance_input.addItems(["1星 (一般)", "2星 (重要)", "3星 (非常重要)"])
        layout.addRow("重要等级:", self.importance_input)
        
        # 任务类别
        self.category_input = QComboBox()
        self.category_input.addItems(self.config["categories"])
        layout.addRow("任务类别:", self.category_input)
        
        # 标签选择（改为下拉选择框）
        self.tags_input = QComboBox()
        self.tags_input.setEditable(False)  # 不可编辑，只能选择
        self.tags_input.setMinimumWidth(150)
        
        # 添加空选项作为默认
        self.tags_input.addItem("（无标签）")
        
        # 添加标签项
        for tag in self.config["tags"]:
            self.tags_input.addItem(tag)
        
        layout.addRow("选择标签:", self.tags_input)

        # 紧急度（1-5级）- 优化显示
        self.urgency_input = QComboBox()
        self.urgency_input.addItems([
            "1-最紧急",
            "2-紧急",
            "3-中等",
            "4-较不紧急",
            "5-最不紧急"
        ])
        self.urgency_input.setMinimumContentsLength(8)
        self.urgency_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addRow("紧急度:", self.urgency_input)

        # 操作按钮（增大尺寸）
        self.add_btn = QPushButton("添加任务")
        self.add_btn.setMinimumHeight(40)  # 增大按钮高度
        self.add_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.add_btn.clicked.connect(self.handle_add_task)
        layout.addRow(self.add_btn)

        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.setMinimumHeight(40)  # 增大按钮高度
        self.refresh_btn.setStyleSheet("font-size: 14px;")
        self.refresh_btn.clicked.connect(self.refresh_all_lists)
        layout.addRow(self.refresh_btn)

        # 设置按钮（增大尺寸）
        self.settings_btn = QPushButton("设置")
        self.settings_btn.setMinimumHeight(40)  # 增大按钮高度
        self.settings_btn.setStyleSheet("font-size: 14px;")
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addRow(self.settings_btn)

        panel.setLayout(layout)
        panel.setMaximumWidth(320)
        return panel
        
    def create_search_filter_panel(self):
        """创建搜索和筛选面板（可折叠，三角形指示器）"""
        # 创建面板并设置为可折叠
        panel = QGroupBox("搜索和筛选")
        panel.setCheckable(True)  # 启用可折叠功能
        panel.setChecked(False)   # 默认折叠状态
        
        # 创建内容容器
        content_widget = QWidget()
        
        # 使用表单布局，一行一个筛选项
        form_layout = QFormLayout(content_widget)
        form_layout.setVerticalSpacing(8)  # 减小垂直间距
        form_layout.setHorizontalSpacing(12)  # 减小水平间距
        form_layout.setFormAlignment(Qt.AlignTop)  # 设置顶部对齐
        form_layout.setLabelAlignment(Qt.AlignLeft)  # 标签左对齐
        
        # 创建搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索任务...")
        self.search_input.setMinimumHeight(28)  # 减小高度
        self.search_input.textChanged.connect(self.handle_search_filter)  # 实时搜索
        form_layout.addRow("搜索任务:", self.search_input)
        
        # 类别筛选
        self.category_filter = QComboBox()
        self.category_filter.addItem("所有类别")
        self.category_filter.addItems(self.config["categories"])
        self.category_filter.setMinimumHeight(28)  # 减小高度
        self.category_filter.setMinimumWidth(150)  # 设置合适宽度
        self.category_filter.currentIndexChanged.connect(self.handle_search_filter)
        form_layout.addRow("类别:", self.category_filter)
        
        # 标签筛选
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("所有标签")
        self.tag_filter.addItem("无标签")
        self.tag_filter.addItems(self.config["tags"])
        self.tag_filter.setMinimumHeight(28)  # 减小高度
        self.tag_filter.setMinimumWidth(150)  # 设置合适宽度
        self.tag_filter.currentIndexChanged.connect(self.handle_search_filter)
        form_layout.addRow("标签:", self.tag_filter)
        
        # 重要等级筛选
        self.importance_filter = QComboBox()
        self.importance_filter.addItem("所有重要度")
        self.importance_filter.addItems(["1星 (一般)", "2星 (重要)", "3星 (非常重要)"])
        self.importance_filter.setMinimumHeight(28)  # 减小高度
        self.importance_filter.setMinimumWidth(150)  # 设置合适宽度
        self.importance_filter.currentIndexChanged.connect(self.handle_search_filter)
        form_layout.addRow("重要等级:", self.importance_filter)
        
        # 紧急度筛选
        self.urgency_filter = QComboBox()
        self.urgency_filter.addItem("所有紧急度")
        self.urgency_filter.addItems([
            "1-最紧急",
            "2-紧急",
            "3-中等",
            "4-较不紧急",
            "5-最不紧急"
        ])
        self.urgency_filter.setMinimumHeight(28)  # 减小高度
        self.urgency_filter.setMinimumWidth(150)  # 设置合适宽度
        self.urgency_filter.currentIndexChanged.connect(self.handle_search_filter)
        form_layout.addRow("紧急度:", self.urgency_filter)
        
        # 截止日期筛选
        self.deadline_filter = QComboBox()
        self.deadline_filter.addItem("所有截止日期")
        self.deadline_filter.addItems([
            "今天",
            "明天",
            "本周内",
            "下周内",
            "本月内",
            "无截止日期"
        ])
        self.deadline_filter.setMinimumHeight(28)  # 减小高度
        self.deadline_filter.setMinimumWidth(150)  # 设置合适宽度
        self.deadline_filter.currentIndexChanged.connect(self.handle_search_filter)
        form_layout.addRow("截止日期:", self.deadline_filter)
        
        # 创建重置按钮
        reset_button = QPushButton("重置筛选")
        reset_button.setMinimumHeight(32)  # 减小高度
        reset_button.setStyleSheet("font-size: 12px;")  # 减小字体
        reset_button.clicked.connect(self.reset_search_filter)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(reset_button)
        
        # 添加按钮布局到表单布局
        form_layout.addRow(button_layout)
        
        # 创建面板的主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(content_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 设置面板布局
        panel.setLayout(main_layout)
        
        # 连接信号，当面板勾选状态改变时更新内容可见性
        panel.toggled.connect(content_widget.setVisible)
        
        # 初始状态下隐藏内容
        content_widget.setVisible(False)
        
        # 返回面板
        return panel

    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            new_config = dialog.get_config()
            # 保存新配置
            if self.config_manager.save_config(new_config):
                self.config = new_config
                # 应用窗口大小设置
                self.resize(self.config["window_width"], self.config["window_height"])
                
                # 更新定时器间隔（秒转换为毫秒）
                new_interval_ms = self.config["update_interval"] * 1000
                self.timer.setInterval(new_interval_ms)
                print(f"定时器间隔已更新为{new_interval_ms}毫秒")
                
                QMessageBox.information(self, "设置成功", "配置已保存")

    def toggle_deadline(self):
        """切换是否启用截止日期"""
        self.deadline_input.setEnabled(not self.no_deadline_btn.isChecked())
        self.one_week_btn.setEnabled(not self.no_deadline_btn.isChecked())
    
    def set_one_week_deadline(self):
        """设置截止时间为一周后"""
        self.no_deadline_btn.setChecked(False)
        self.deadline_input.setDateTime(QDateTime.currentDateTime().addDays(7))
    


    def handle_add_task(self):
        """处理添加任务"""
        name = self.task_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入事务名称")
            return

        # 获取截止日期时间
        if self.no_deadline_btn.isChecked():
            deadline = "无截止日期"
        else:
            deadline = self.deadline_input.dateTime().toString("yyyy-MM-dd HH:mm")

        # 获取重要等级（1-3星）
        importance = self.importance_input.currentIndex() + 1

        # 紧急度获取
        try:
            selected_text = self.urgency_input.currentText().strip()
            urgency = int(selected_text.split("-")[0])
            if urgency < 1 or urgency > 5:
                raise ValueError("紧急度必须在1-5之间")
        except (ValueError, IndexError) as e:
            QMessageBox.warning(self, "输入错误", f"请选择有效的紧急度：{str(e)}")
            return
        
        # 获取任务类别和标签（下拉选择框）
        category = self.category_input.currentText()
        tags = []
        if hasattr(self, 'tags_input'):
            selected_tag = self.tags_input.currentText()
            if selected_tag and selected_tag != "（无标签）":
                tags = [selected_tag]  # 转换为列表格式以兼容现有代码

        # 计算任务应有的紧急度（基于截止时间）
        proper_urgency = urgency  # 默认使用用户设置的紧急度
        if deadline != "无截止日期":
            deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
            now = datetime.now()
            time_diff = deadline_dt - now
            days_remaining = time_diff.total_seconds() / (24 * 3600)
            
            # 根据剩余天数计算正确的紧急度
            if days_remaining <= 0:
                proper_urgency = 1
            elif days_remaining <= 1:
                proper_urgency = 2
            elif days_remaining <= 3:
                proper_urgency = 3
            elif days_remaining <= 7:
                proper_urgency = 4
            else:
                proper_urgency = 5
        
        # 添加任务
        self.task_handler.add_task({
            "name": name,
            "deadline": deadline,
            "importance": importance,
            "urgency": urgency,
            "category": category,
            "tags": tags
        })

        # 只有当需要提升紧急度时才设置创建任务标志
        self._is_creating_task = (proper_urgency < urgency)

        # 刷新所有列表（会自动调用auto_promote_urgency并处理紧急度升级通知）
        self.task_name_input.clear()
        self.show_system_tray_message(
            "任务已添加",
            f"成功添加：{name}（紧急度：{urgency}，重要度：{importance}星）"
        )
        # 调用refresh_all_lists而不是仅refresh_list("todo")，以确保紧急度升级逻辑被执行
        self.refresh_all_lists()

    def handle_mark_done(self, task_type):
        """处理标记完成"""
        list_widget = getattr(self, f"{task_type}_list")
        index = list_widget.get_selected_index()

        if index == -1:
            QMessageBox.warning(self, "提示", "请选择一个任务")
            return

        # 获取任务名称用于提示
        tasks = self.task_handler.get_sorted_tasks(task_type)
        task_name = tasks[index]["name"]

        if self.task_handler.mark_as_done(task_type, index):
            self.refresh_list(task_type)
            self.refresh_list("done")
            self.show_system_tray_message("任务已完成", f"已完成：{task_name}")

    def handle_delete(self, task_type):
        """处理删除任务"""
        list_widget = getattr(self, f"{task_type}_list")
        index = list_widget.get_selected_index()

        if index == -1:
            QMessageBox.warning(self, "提示", "请选择一个任务")
            return

        # 获取任务名称用于提示
        tasks = self.task_handler.get_sorted_tasks(task_type)
        task_name = tasks[index]["name"]

        # 确认删除
        reply = QMessageBox.question(
            self, "确认", "确定要删除选中的任务吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes and self.task_handler.delete_task(task_type, index):
            self.refresh_list(task_type)
            self.show_system_tray_message("任务已删除", f"已删除：{task_name}")

    def format_task_text(self, task):
        """格式化任务显示文本，包含创建时间、截止日期、类别、标签和倒计时信息"""
        stars = "★" * task["importance"] + "☆" * (3 - task["importance"])
        # 计算并获取倒计时信息
        time_remaining = self.task_handler.calculate_time_remaining(task)
        
        # 获取创建时间和截止日期
        create_time = task.get('create_time', '')
        deadline = task.get('deadline', '无截止日期')
        
        # 构建任务文本
        text = (
            f"{task['name']}\n" 
            f"重要度: {stars} | 紧急度: {task['urgency']}\n" 
            f"创建时间: {create_time}\n"
            f"截止日期: {deadline}\n"
        )
        
        # 添加类别信息
        if 'category' in task and task['category']:
            text += f"类别: {task['category']}\n"
        
        # 添加标签信息
        if 'tags' in task and task['tags']:
            tags_text = ', '.join(task['tags'])
            text += f"标签: {tags_text}\n"
        
        # 添加倒计时信息（最后一行，保持原有的颜色逻辑）
        text += f"{time_remaining}"
        
        return text

    def handle_search_filter(self):
        """处理搜索和筛选操作"""
        self.refresh_all_lists()
        
    def reset_search_filter(self):
        """重置所有筛选条件"""
        self.search_input.clear()
        self.category_filter.setCurrentIndex(0)
        self.tag_filter.setCurrentIndex(0)
        self.importance_filter.setCurrentIndex(0)
        self.urgency_filter.setCurrentIndex(0)
        self.deadline_filter.setCurrentIndex(0)
        
    def filter_tasks(self, tasks):
        """根据搜索和筛选条件过滤任务列表"""
        # 获取搜索和筛选条件
        search_text = self.search_input.text().lower().strip()
        selected_category = self.category_filter.currentText()
        selected_tag = self.tag_filter.currentText()
        selected_importance = self.importance_filter.currentText()
        selected_urgency = self.urgency_filter.currentText()
        selected_deadline = self.deadline_filter.currentText()
        
        filtered_tasks = []
        
        for task in tasks:
            # 关键词搜索
            if search_text and search_text not in task["name"].lower():
                continue
                
            # 类别筛选
            if selected_category != "所有类别" and task.get("category", "") != selected_category:
                continue
                
            # 标签筛选
            if selected_tag != "所有标签":
                task_tags = task.get("tags", [])
                if selected_tag == "无标签" and task_tags:
                    continue
                elif selected_tag != "无标签" and selected_tag not in task_tags:
                    continue
                    
            # 重要等级筛选
            if selected_importance != "所有重要度":
                importance_level = int(selected_importance.split("星")[0])
                if task["importance"] != importance_level:
                    continue
                    
            # 紧急度筛选
            if selected_urgency != "所有紧急度":
                urgency_level = int(selected_urgency.split("-")[0])
                if task["urgency"] != urgency_level:
                    continue
                    
            # 截止日期筛选
            if selected_deadline != "所有截止日期":
                task_deadline = task.get("deadline", "无截止日期")
                
                if selected_deadline == "无截止日期":
                    if task_deadline != "无截止日期":
                        continue
                else:
                    if task_deadline == "无截止日期":
                        continue
                    
                    # 解析截止日期
                    try:
                        # 尝试解析包含时间的格式
                        try:
                            deadline_datetime = datetime.strptime(task_deadline, "%Y-%m-%d %H:%M")
                        except ValueError:
                            # 回退到旧格式（仅日期）
                            deadline_datetime = datetime.strptime(task_deadline, "%Y-%m-%d")
                        
                        now = datetime.now()
                        today = now.date()
                        tomorrow = today + timedelta(days=1)
                        
                        # 本周开始和结束（周一到周日）
                        days_since_monday = today.weekday()
                        week_start = today - timedelta(days=days_since_monday)
                        week_end = week_start + timedelta(days=7)
                        
                        # 下周开始和结束
                        next_week_start = week_start + timedelta(days=7)
                        next_week_end = next_week_start + timedelta(days=7)
                        
                        # 本月开始和结束
                        month_start = date(today.year, today.month, 1)
                        if today.month == 12:
                            month_end = date(today.year + 1, 1, 1)
                        else:
                            month_end = date(today.year, today.month + 1, 1)
                        
                        # 检查截止日期是否符合条件
                        deadline_date = deadline_datetime.date()
                        
                        if selected_deadline == "今天" and deadline_date != today:
                            continue
                        elif selected_deadline == "明天" and deadline_date != tomorrow:
                            continue
                        elif selected_deadline == "本周内" and not (week_start <= deadline_date < week_end):
                            continue
                        elif selected_deadline == "下周内" and not (next_week_start <= deadline_date < next_week_end):
                            continue
                        elif selected_deadline == "本月内" and not (month_start <= deadline_date < month_end):
                            continue
                    except Exception:
                        # 日期格式错误，跳过该任务
                        continue
                        
            # 通过所有筛选条件
            filtered_tasks.append(task)
            
        return filtered_tasks
        
    def refresh_list(self, task_type):
        list_widget = getattr(self, f"{task_type}_list")
        list_widget.clear_list()

        tasks = self.task_handler.get_sorted_tasks(task_type)
        
        # 应用搜索和筛选
        filtered_tasks = self.filter_tasks(tasks)
        task_count = len(filtered_tasks)

        group_widget = getattr(self, f"{task_type}_group")
        group_widget.setTitle(f"{group_widget.title().split('(')[0]}({task_count})")

        for index, task in enumerate(filtered_tasks, 1):
            list_widget.add_task_item(
                self.format_task_text(task),
                index=index,
                urgency=task["urgency"],
                is_overdue=(task_type == "overdue"),
                is_done=(task_type == "done")
            )

    def refresh_all_lists(self):
        """刷新所有列表"""
        self.task_handler.check_overdue_tasks()
        
        # 获取自动提升紧急度的任务列表
        promoted_tasks = self.task_handler.auto_promote_urgency()
        
        # 显示提升紧急度的托盘通知
        if promoted_tasks and len(promoted_tasks) > 0:
            if len(promoted_tasks) == 1:
                task = promoted_tasks[0]
                message = f"'{task['name']}'\n紧急度从{task['old_urgency']}提升到{task['new_urgency']}\n{task.get('reason', '')}"
                # 判断是否是创建任务时的升级
                is_creating = hasattr(self, '_is_creating_task') and self._is_creating_task
                title = "创建任务并自动升级紧急度" if is_creating else "任务紧急度提升"
                self.show_system_tray_message(title, message)
                # 重置标志
                if is_creating:
                    delattr(self, '_is_creating_task')
            else:
                # 多个任务时显示简洁信息
                task_details = ""
                for i, task in enumerate(promoted_tasks[:3], 1):  # 最多显示前3个任务详情
                    task_details += f"{i}. '{task['name']}': {task['old_urgency']}→{task['new_urgency']}\n"
                if len(promoted_tasks) > 3:
                    task_details += f"... 还有{len(promoted_tasks)-3}个任务"
                message = f"共有{len(promoted_tasks)}个任务紧急度已提升\n{task_details}"
                self.show_system_tray_message("多个任务紧急度提升", message)
        
        self.refresh_list("todo")
        self.refresh_list("overdue")
        self.refresh_list("done")

    # 系统托盘相关方法
    def show_system_tray_message(self, title, message):
        """显示托盘消息（根据配置决定是否显示）"""
        if self.config["show_notifications"]:
            self.tray_icon.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                2000  # 显示2秒
            )

    def on_tray_activated(self, reason):
        """托盘图标被点击时"""
        if reason == QSystemTrayIcon.Trigger:  # 左键点击
            self.toggle_window_visibility()

    def toggle_window_visibility(self):
        """切换窗口显示/隐藏"""
        if self.isHidden():
            self.show_window()
        else:
            self.hide_window()

    def show_window(self):
        """显示窗口"""
        self.show()
        self.raise_()  # 置顶窗口
        self.activateWindow()  # 激活窗口
        self.show_system_tray_message("窗口已显示", "使用 Ctrl+Alt+T 隐藏窗口")

    def hide_window(self):
        """隐藏窗口"""
        self.hide()
        self.show_system_tray_message("窗口已隐藏", "使用 Ctrl+Alt+T 呼出窗口")

    def init_timer(self):
        """初始化定时器用于刷新倒计时显示"""
        self.timer = QTimer(self)
        # 从配置中获取更新间隔（秒转换为毫秒）
        interval_ms = self.config["update_interval"] * 1000
        self.timer.setInterval(interval_ms)
        print(f"定时器已初始化，间隔设置为{interval_ms}毫秒")
        # 连接信号到刷新方法
        self.timer.timeout.connect(self.refresh_time_display)
        # 启动定时器
        self.timer.start()
        print("定时器已启动")
    
    def refresh_time_display(self):
        """刷新任务时间显示，但不进行完整的列表排序和保存"""
        # 只刷新待办和超时列表的显示，避免频繁的完整刷新影响性能
        print(f"定时器触发刷新时间显示: {time.strftime('%H:%M:%S')}")  # 添加调试日志
        for task_type in ["todo", "overdue"]:
            list_widget = getattr(self, f"{task_type}_list")
            list_widget.clear_list()
            
            tasks = self.task_handler.get_sorted_tasks(task_type)  # 这里会更新紧急度
            for index, task in enumerate(tasks, 1):
                list_widget.add_task_item(
                    self.format_task_text(task),
                    index=index,
                    urgency=task["urgency"],
                    is_overdue=(task_type == "overdue"),
                    is_done=(task_type == "done")
                )
    
    def exit_app(self):
        """退出应用"""
        self.timer.stop()  # 停止定时器
        self.data_manager.save_tasks(self.task_handler.tasks)
        self.tray_icon.hide()  # 隐藏托盘图标
        qApp.quit()  # 退出应用

    def closeEvent(self, event):
        """窗口关闭事件（改为隐藏到托盘）"""
        event.ignore()  # 忽略关闭事件
        self.hide_window()  # 隐藏窗口而不是退出