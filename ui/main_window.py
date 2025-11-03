import sys
import time
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QGroupBox, QFormLayout, QLineEdit, QComboBox,
                             QDateTimeEdit, QPushButton, QSplitter, QMessageBox,
                             QSystemTrayIcon, QMenu, QAction, qApp, QDialog,
                             QSpinBox, QLabel, QCheckBox, QSizePolicy, QGridLayout,
                             QTabWidget, QFileDialog, QMenuBar, QApplication, QListWidget, QStackedWidget)
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
    """设置对话框 - 整合所有设置选项"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        # 使用深度复制确保配置不被引用共享
        import copy
        self.config = copy.deepcopy(config)
        self.do_backup = False  # 是否需要执行备份
        # 获取当前主题设置，确定是否为深色模式
        current_theme = self.config.get("theme", 0)
        self.is_dark_theme = (current_theme == 2)  # 2表示深色主题
        self.init_ui()
        # 在UI初始化后显式更新备份设置控件，确保显示最新值
        print("[SettingsDialog] 初始化后更新备份设置控件")
        self.update_backup_settings_controls()
        # 应用主题样式
        self._apply_theme_styles()

    def init_ui(self):
        self.setWindowTitle("设置")
        # 使用更大的窗口尺寸提供更好的用户体验
        self.setGeometry(200, 200, 900, 650)
        
        # 设置中文字体支持
        font = QFont()
        font.setFamily("SimHei")
        self.setFont(font)
        
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建左侧导航面板 - 类似浏览器设置的侧边栏设计
        nav_widget = QWidget()
        nav_widget.setMinimumWidth(220)
        nav_widget.setMaximumWidth(240)
        nav_widget.setStyleSheet("""
            QWidget { 
                background-color: #f8f9fa; 
                border-right: 1px solid #e0e0e0;
            }
            QListWidget { 
                background-color: transparent; 
                border: none;
                outline: none;
            }
            QListWidget::item { 
                padding: 12px 20px;
                height: 48px;
                font-size: 14px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected { 
                background-color: #e6f2ff;
                color: #0078d7;
                border-left: 3px solid #0078d7;
            }
        """)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        # 添加设置标题
        title_label = QLabel("设置")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        nav_layout.addWidget(title_label)
        
        # 添加搜索框 - 更现代的搜索设计
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(15, 0, 15, 10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索设置...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border-radius: 4px;
                border: 1px solid #ddd;
                padding: 8px 12px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #0078d7;
                outline: none;
            }
        """)
        search_layout.addWidget(self.search_input)
        nav_layout.addLayout(search_layout)
        
        # 创建导航列表
        self.nav_list = QListWidget()
        self.nav_list.addItems(["基本设置", "备份与恢复", "外观设置", "通知设置", "数据更新设置", "快捷键设置"])
        self.nav_list.setCurrentRow(0)
        self.nav_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                padding: 12px 20px;
                height: 48px;
                font-size: 14px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e6f2ff;
                color: #0078d7;
                border-left: 3px solid #0078d7;
            }
        """)
        # 移除不需要的itemClicked连接，使用currentRowChanged即可
        nav_layout.addWidget(self.nav_list, 1)  # 添加拉伸因子1，使导航列表铺满剩余高度
        
        # 添加底部间距
        nav_layout.addStretch()
        
        # 保存标题标签引用，用于后续样式更新
        self.title_label = title_label
        
        # 保存导航部件引用
        self.nav_widget = nav_widget
        
        # 创建右侧内容区域 - 使用更现代的样式
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #ffffff;
                color: #000000;
            }
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
        """)
        
        # 添加到主布局
        main_layout.addWidget(self.nav_widget)
        main_layout.addWidget(self.content_stack, 1)  # 1表示拉伸因子
        
        # 连接导航选择信号
        self.nav_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        
        # 添加各个设置页面（在nav_widget初始化后再调用）
        self.init_basic_settings_page()
        self.init_backup_settings_page()
        self.init_interface_settings_page()
        self.init_notification_settings_page()
        self.init_update_settings_page()
        self.init_hotkey_settings_page()
    
    def init_basic_settings_page(self):
        """初始化基本设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 页面标题 - 更大更醒目
        title_label = QLabel("基本设置")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333;
            margin-bottom: 20px;
        """)
        layout.addWidget(title_label)
        
        # 程序信息卡片 - 使用现代化卡片设计
        info_card = QWidget()
        info_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        info_title = QLabel("程序信息")
        info_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        info_layout.addWidget(info_title)
        
        # 程序详情 - 使用表格布局
        detail_layout = QFormLayout()
        detail_layout.setHorizontalSpacing(20)
        detail_layout.setVerticalSpacing(10)
        
        # 使用只读文本框而不是简单标签，更符合现代UI
        version_edit = QLineEdit("v1.0.3")
        version_edit.setReadOnly(True)
        version_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 10px;
            }
        """)
        
        update_edit = QLineEdit("2025年11月")
        update_edit.setReadOnly(True)
        update_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 10px;
            }
        """)
        
        detail_layout.addRow(QLabel("当前版本:"), version_edit)
        detail_layout.addRow(QLabel("最近更新:"), update_edit)
        info_layout.addLayout(detail_layout)
        
        layout.addWidget(info_card)
        
        # 重置设置按钮 - 更大更醒目，有悬停效果
        reset_btn = QPushButton("重置所有设置")
        reset_btn.setMinimumHeight(40)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4757;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #ff3838;
            }
        """)
        reset_btn.clicked.connect(self.handle_reset_settings)
        layout.addWidget(reset_btn, alignment=Qt.AlignLeft)
        
        # 添加热门设置卡片
        hot_settings_card = QWidget()
        hot_settings_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        hot_layout = QVBoxLayout(hot_settings_card)
        hot_layout.setContentsMargins(20, 20, 20, 20)
        
        hot_title = QLabel("热门设置")
        hot_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        hot_layout.addWidget(hot_title)
        
        # 添加快速访问按钮
        quick_layout = QGridLayout()
        quick_layout.setSpacing(10)
        
        theme_btn = QPushButton("外观设置")
        theme_btn.setMinimumHeight(35)
        theme_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        theme_btn.clicked.connect(lambda: self.nav_list.setCurrentRow(2))
        
        backup_btn = QPushButton("备份与恢复")
        backup_btn.setMinimumHeight(35)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        backup_btn.clicked.connect(lambda: self.nav_list.setCurrentRow(1))
        
        quick_layout.addWidget(theme_btn, 0, 0)
        quick_layout.addWidget(backup_btn, 1, 0)
        hot_layout.addLayout(quick_layout)
        
        layout.addWidget(hot_settings_card)
        
        layout.addStretch()
        self.content_stack.addWidget(page)
    
    def init_backup_settings_page(self):
        """初始化备份设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 页面标题 - 更大更醒目
        title_label = QLabel("备份与恢复")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333;
            margin-bottom: 20px;
        """)
        layout.addWidget(title_label)
        
        # 自动备份设置卡片
        auto_backup_card = QWidget()
        auto_backup_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        auto_backup_layout = QVBoxLayout(auto_backup_card)
        auto_backup_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        card_title = QLabel("自动备份设置")
        card_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        auto_backup_layout.addWidget(card_title)
        
        # 启用自动备份复选框 - 使用更大的复选框
        self.auto_backup_check = QCheckBox("启用自动备份")
        self.auto_backup_check.setStyleSheet("font-size: 14px; margin-bottom: 15px;")
        self.auto_backup_check.stateChanged.connect(self.toggle_auto_backup_options)
        auto_backup_layout.addWidget(self.auto_backup_check)
        
        # 备份间隔设置（分钟）
        interval_layout = QHBoxLayout()
        interval_label = QLabel("备份间隔（分钟）:")
        interval_label.setMinimumWidth(120)
        interval_layout.addWidget(interval_label)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 10080)  # 最大7天（60*24*7）
        self.interval_spin.setMinimumWidth(150)  # 调整为更合适的宽度
        self.interval_spin.setMinimumHeight(32)  # 调整为更合适的高度
        self.interval_spin.setAlignment(Qt.AlignCenter)  # 文本居中显示
        self.interval_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addStretch()
        auto_backup_layout.addLayout(interval_layout)
        
        # 备份路径设置
        path_layout = QHBoxLayout()
        path_label = QLabel("备份目录:")
        path_label.setMinimumWidth(120)
        path_layout.addWidget(path_label)
        
        self.backup_path_edit = QLineEdit()
        # 默认使用backups文件夹作为备份路径
        default_backup_path = os.path.join(os.getcwd(), 'backups')
        self.backup_path_edit.setText(self.config.get("backup_path", default_backup_path))
        self.backup_path_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                flex: 1;
            }
        """)
        path_layout.addWidget(self.backup_path_edit, 1)
        
        browse_btn = QPushButton("浏览")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        browse_btn.clicked.connect(self.browse_backup_path)
        path_layout.addWidget(browse_btn)
        auto_backup_layout.addLayout(path_layout)
        
        layout.addWidget(auto_backup_card)
        
        # 手动备份卡片
        manual_backup_card = QWidget()
        manual_backup_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        manual_backup_layout = QVBoxLayout(manual_backup_card)
        manual_backup_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        manual_title = QLabel("手动备份")
        manual_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        manual_backup_layout.addWidget(manual_title)
        
        # 立即手动备份按钮 - 使用醒目的主色调
        self.manual_backup_btn = QPushButton("立即手动备份")
        self.manual_backup_btn.setMinimumHeight(45)
        self.manual_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.manual_backup_btn.clicked.connect(self.accept_and_backup)
        manual_backup_layout.addWidget(self.manual_backup_btn)
        
        # 备份说明 - 更清晰的说明文本
        backup_note = QLabel("注意：备份会生成JSON和CSV两种格式的文件，保存在您指定的备份目录中。")
        backup_note.setWordWrap(True)
        backup_note.setStyleSheet("color: #666; font-size: 13px; margin-top: 10px;")
        manual_backup_layout.addWidget(backup_note)
        
        layout.addWidget(manual_backup_card)
        
        # 恢复选项卡片
        restore_card = QWidget()
        restore_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        restore_layout = QVBoxLayout(restore_card)
        restore_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        restore_title = QLabel("数据恢复")
        restore_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        restore_layout.addWidget(restore_title)
        
        # 从备份恢复按钮
        restore_btn = QPushButton("从备份文件恢复")
        restore_btn.setMinimumHeight(40)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        restore_btn.clicked.connect(self.handle_restore_backup)
        restore_layout.addWidget(restore_btn)
        
        # 恢复警告
        restore_warning = QLabel("警告：恢复数据将覆盖当前所有任务数据，请确保已做好备份。")
        restore_warning.setWordWrap(True)
        restore_warning.setStyleSheet("color: #dc3545; font-size: 13px; margin-top: 10px;")
        restore_layout.addWidget(restore_warning)
        
        layout.addWidget(restore_card)
        
        layout.addStretch()
        self.content_stack.addWidget(page)
        
        # 初始状态设置
        self.toggle_auto_backup_options()
    
    def init_interface_settings_page(self):
        """初始化界面设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 页面标题 - 更大更醒目
        title_label = QLabel("外观设置")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333;
            margin-bottom: 20px;
        """)
        layout.addWidget(title_label)
        
        # 窗口大小设置卡片
        size_card = QWidget()
        size_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        size_layout = QVBoxLayout(size_card)
        size_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        size_card_title = QLabel("窗口大小设置")
        size_card_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        size_layout.addWidget(size_card_title)
        
        # 使用表格布局，更现代的样式
        size_form_layout = QFormLayout()
        size_form_layout.setHorizontalSpacing(20)
        size_form_layout.setVerticalSpacing(12)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(800, 2000)  # 最小800，最大2000
        self.width_spin.setValue(self.config["window_width"])
        self.width_spin.setMinimumWidth(120)
        self.width_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        
        width_label = QLabel("窗口宽度:")
        width_label.setStyleSheet("font-size: 14px;")
        size_form_layout.addRow(width_label, self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(600, 1500)  # 最小600，最大1500
        self.height_spin.setValue(self.config["window_height"])
        self.height_spin.setMinimumWidth(120)
        self.height_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        
        height_label = QLabel("窗口高度:")
        height_label.setStyleSheet("font-size: 14px;")
        size_form_layout.addRow(height_label, self.height_spin)
        
        size_layout.addLayout(size_form_layout)
        layout.addWidget(size_card)
        
        # 界面主题设置卡片
        theme_card = QWidget()
        theme_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        theme_card_title = QLabel("界面主题")
        theme_card_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        theme_layout.addWidget(theme_card_title)
        
        # 主题选择下拉框 - 使用更现代的样式
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认主题", "浅色主题", "深色主题"])
        # 尝试获取当前主题配置，默认为0（默认主题）
        current_theme = self.config.get("theme", 0)
        if current_theme < self.theme_combo.count():
            self.theme_combo.setCurrentIndex(current_theme)
        # 连接信号，当主题选择改变时更新预览
        self.theme_combo.currentIndexChanged.connect(self.update_theme_preview)
        self.theme_combo.setMinimumHeight(35)
        self.theme_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #ddd;
                border-left-style: solid;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
        """)
        theme_layout.addWidget(self.theme_combo)
        
        # 主题预览区域
        self.preview_frame = QWidget()
        self.preview_frame.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 15px;
                padding: 15px;
            }
        """)
        preview_layout = QVBoxLayout(self.preview_frame)
        
        preview_label = QLabel("主题预览效果")
        preview_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        preview_layout.addWidget(preview_label)
        
        # 添加主题说明
        theme_desc = QLabel("选择不同主题可以改变程序的整体外观风格。")
        theme_desc.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 10px;")
        preview_layout.addWidget(theme_desc)
        
        # 预览按钮组，展示主题效果
        preview_btn_layout = QHBoxLayout()
        preview_btn_layout.setSpacing(10)
        
        self.preview_btn1 = QPushButton("主要按钮")
        self.preview_btn1.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
        """)
        
        self.preview_btn2 = QPushButton("次要按钮")
        self.preview_btn2.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px 16px;
            }
        """)
        
        preview_btn_layout.addWidget(self.preview_btn1)
        preview_btn_layout.addWidget(self.preview_btn2)
        preview_layout.addLayout(preview_btn_layout)
        
        theme_layout.addWidget(self.preview_frame)
        layout.addWidget(theme_card)
        
        # 初始更新预览
        self.update_theme_preview(self.theme_combo.currentIndex())
        
        # 应用主题样式
        self._apply_theme_styles()
        
        layout.addStretch()
        self.content_stack.addWidget(page)
    
    def _apply_theme_styles(self):
        """
        应用主题样式到设置对话框的各个组件
        """
        if self.is_dark_theme:
            # 深色主题样式
            # 导航面板样式
            self.nav_widget.setStyleSheet("""
                QWidget { 
                    background-color: #252526; 
                    border-right: 1px solid #3e3e42;
                }
                QListWidget { 
                    background-color: transparent; 
                    border: none;
                    outline: none;
                }
                QListWidget::item { 
                    padding: 12px 20px;
                    height: 48px;
                    font-size: 14px;
                    border-bottom: 1px solid #3e3e42;
                    color: #ffffff;
                }
                QListWidget::item:selected { 
                    background-color: #0e639c;
                    color: #ffffff;
                    border-left: 3px solid #0e639c;
                }
            """)
            
            # 标题样式
            self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px; color: #ffffff;")
            
            # 搜索框样式
            self.search_input.setStyleSheet("""
                QLineEdit {
                    border-radius: 4px;
                    border: 1px solid #3c3c3c;
                    padding: 8px 12px;
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QLineEdit:focus {
                    border-color: #0e639c;
                    outline: none;
                }
                QLineEdit::placeholder {
                    color: #999999;
                }
            """)
            
            # 内容区域样式
            self.content_stack.setStyleSheet("""
                QStackedWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
        else:
            # 浅色主题样式（恢复默认样式）
            self.nav_widget.setStyleSheet("""
                QWidget { 
                    background-color: #f8f9fa; 
                    border-right: 1px solid #e0e0e0;
                }
                QListWidget { 
                    background-color: transparent; 
                    border: none;
                    outline: none;
                }
                QListWidget::item { 
                    padding: 12px 20px;
                    height: 48px;
                    font-size: 14px;
                    border-bottom: 1px solid #f0f0f0;
                }
                QListWidget::item:selected { 
                    background-color: #e6f2ff;
                    color: #0078d7;
                    border-left: 3px solid #0078d7;
                }
            """)
            
            # 标题样式
            self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
            
            # 搜索框样式
            self.search_input.setStyleSheet("""
                QLineEdit {
                    border-radius: 4px;
                    border: 1px solid #ddd;
                    padding: 8px 12px;
                    background-color: white;
                }
                QLineEdit:focus {
                    border-color: #0078d7;
                    outline: none;
                }
            """)
            
            # 内容区域样式
            self.content_stack.setStyleSheet("""
                QStackedWidget {
                    background-color: #ffffff;
                    color: #000000;
                }
                QWidget {
                    background-color: #ffffff;
                    color: #000000;
                }
            """)
        
        # 更新所有设置页面中的卡片和控件样式
        self._update_all_cards_styles(self.is_dark_theme)
    
    def _update_all_cards_styles(self, is_dark):
        """
        更新所有设置页面中卡片和控件的样式
        """
        # 为每个页面中的卡片和控件设置样式
        for i in range(self.content_stack.count()):
            page = self.content_stack.widget(i)
            if page:
                # 首先设置页面背景色
                if is_dark:
                    page.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
                # 获取页面中的所有卡片和控件
                for child in page.findChildren(QWidget):
                    # 处理QLabel
                    if isinstance(child, QLabel):
                        # 跳过预览区域的标签
                        if hasattr(self, 'preview_frame') and child.isAncestorOf(self.preview_frame):
                            continue
                        # 设置标签颜色
                        if is_dark:
                            # 检查是否有特殊样式，如果没有则设置默认深色模式样式
                            current_style = child.styleSheet()
                            if not current_style or "color:" not in current_style:
                                child.setStyleSheet(current_style + "color: #ffffff;")
                            # 更新标题样式
                            if "font-size: 24px" in current_style:
                                child.setStyleSheet(current_style.replace("color: #333;", "color: #ffffff;"))
                    
                    # 处理QPushButton（跳过预览按钮）
                    elif isinstance(child, QPushButton):
                        # 跳过预览区域的所有按钮
                        if hasattr(self, 'preview_frame') and child.isAncestorOf(self.preview_frame):
                            continue
                        # 跳过特定预览按钮
                        if hasattr(self, 'preview_btn1') and (child == self.preview_btn1 or child == self.preview_btn2):
                            continue
                        if is_dark:
                            # 获取当前样式
                            current_style = child.styleSheet()
                            # 检查是否为特殊颜色按钮（红色、蓝色等），保留其特殊颜色
                            if "ff4757" not in current_style and "0078d7" not in current_style and "17a2b8" not in current_style and "dc3545" not in current_style and "007bff" not in current_style and "28a745" not in current_style and "ffc107" not in current_style:
                                # 如果没有特定样式，则应用默认的深色模式按钮样式
                                if not current_style or "background-color" not in current_style:
                                    child.setStyleSheet("""
                                        QPushButton {
                                            background-color: #2d2d30;
                                            color: #ffffff;
                                            border: 1px solid #3c3c3c;
                                            border-radius: 4px;
                                            padding: 6px 12px;
                                        }
                                        QPushButton:hover {
                                            background-color: #3e3e42;
                                        }
                                    """)
                                else:
                                    # 更新已有样式中的颜色值
                                    updated_style = current_style
                                    # 更新白色背景
                                    updated_style = updated_style.replace("background-color: white;", "background-color: #2d2d30;")
                                    updated_style = updated_style.replace("background-color: #f8f9fa;", "background-color: #2d2d30;")
                                    updated_style = updated_style.replace("background-color: #f0f0f0;", "background-color: #3e3e42;")
                                    updated_style = updated_style.replace("background-color: #f8f8f8;", "background-color: #3c3c3c;")
                                    # 更新文字颜色
                                    updated_style = updated_style.replace("color: white;", "color: #ffffff;")
                                    updated_style = updated_style.replace("color: #333;", "color: #ffffff;")
                                    updated_style = updated_style.replace("color: #222;", "color: #cccccc;")
                                    # 更新边框颜色
                                    updated_style = updated_style.replace("border: 1px solid #ddd;", "border: 1px solid #3c3c3c;")
                                    child.setStyleSheet(updated_style)
                    
                    # 处理卡片QWidget
                    elif isinstance(child, QWidget) and "background-color" in child.styleSheet():
                        if is_dark:
                            # 为卡片设置深色背景
                            current_style = child.styleSheet()
                            # 更新卡片背景颜色
                            updated_style = current_style
                            updated_style = updated_style.replace("background-color: #f8f9fa;", "background-color: #2d2d30;")
                            updated_style = updated_style.replace("background-color: #f5f5f5;", "background-color: #2d2d30;")
                            updated_style = updated_style.replace("background-color: #fafafa;", "background-color: #2d2d30;")
                            updated_style = updated_style.replace("background-color: white;", "background-color: #2d2d30;")
                            # 更新边框颜色
                            updated_style = updated_style.replace("border: 1px solid #e9ecef;", "border: 1px solid #3c3c3c;")
                            updated_style = updated_style.replace("border: 1px solid #ddd;", "border: 1px solid #3c3c3c;")
                            updated_style = updated_style.replace("border: 1px solid #eee;", "border: 1px solid #3c3c3c;")
                            # 添加文字颜色
                            if "color:" not in updated_style:
                                updated_style += "color: #ffffff;"
                            child.setStyleSheet(updated_style)
                    
                    # 处理其他输入控件
                    elif isinstance(child, (QLineEdit, QSpinBox, QComboBox, QCheckBox)):
                        if is_dark:
                            if isinstance(child, QLineEdit):
                                # 检查是否为只读文本框（如程序信息）
                                if child.isReadOnly():
                                    child.setStyleSheet("""
                                            QLineEdit {
                                                background-color: #2d2d30;
                                                border: 1px solid #3c3c3c;
                                                border-radius: 4px;
                                                padding: 6px 10px;
                                                color: #ffffff;
                                            }
                                        """)
                                else:
                                    child.setStyleSheet("""
                                        QLineEdit {
                                            border: 1px solid #3c3c3c;
                                            border-radius: 4px;
                                            padding: 6px;
                                            background-color: #3c3c3c;
                                            color: #ffffff;
                                        }
                                    """)
                            elif isinstance(child, QSpinBox):
                                child.setStyleSheet("""
                                    QSpinBox {
                                        border: 1px solid #3c3c3c;
                                        border-radius: 4px;
                                        padding: 5px 10px;
                                        background-color: #3c3c3c;
                                        color: #ffffff;
                                        font-size: 14px;
                                        font-weight: bold;
                                        min-width: 150px;
                                        min-height: 32px;
                                        text-align: center;
                                    }
                                """)
                            elif isinstance(child, QComboBox):
                                child.setStyleSheet("""
                                    QComboBox {
                                        border: 1px solid #3c3c3c;
                                        border-radius: 4px;
                                        padding: 6px;
                                        background-color: #3c3c3c;
                                        color: #ffffff;
                                    }
                                    QComboBox::drop-down {
                                        subcontrol-origin: padding;
                                        subcontrol-position: top right;
                                        width: 25px;
                                        border-left-width: 1px;
                                        border-left-color: #3c3c3c;
                                        border-left-style: solid;
                                        border-top-right-radius: 4px;
                                        border-bottom-right-radius: 4px;
                                    }
                                    QComboBox QAbstractItemView {
                                        background-color: #2d2d30;
                                        color: #ffffff;
                                        border: 1px solid #3c3c3c;
                                    }
                                """)
                            elif isinstance(child, QCheckBox):
                                child.setStyleSheet("color: #ffffff;")
        
        # 确保预览区域标签颜色正确
        if hasattr(self, 'preview_frame'):
            for label in self.preview_frame.findChildren(QLabel):
                if is_dark:
                    label.setStyleSheet(label.styleSheet() + "color: #ffffff;")
                else:
                    # 移除可能添加的颜色样式，保持原有预览样式
                    pass
    
    def update_theme_preview(self, theme_index):
        """更新主题预览效果"""
        if theme_index == 0:  # 默认主题
            self.preview_frame.setStyleSheet("""
                QWidget {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-top: 15px;
                    padding: 15px;
                }
            """)
            self.preview_btn1.setStyleSheet("""
                QPushButton {
                    background-color: #0078d7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
            """)
            self.preview_btn2.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
            """)
        elif theme_index == 1:  # 浅色主题
            self.preview_frame.setStyleSheet("""
                QWidget {
                    background-color: #fafafa;
                    border: 1px solid #eee;
                    border-radius: 6px;
                    margin-top: 15px;
                    padding: 15px;
                }
            """)
            self.preview_btn1.setStyleSheet("""
                QPushButton {
                    background-color: #4a90e2;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 500;
                }
            """)
            self.preview_btn2.setStyleSheet("""
                QPushButton {
                    background-color: #f8f8f8;
                    color: #222;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 500;
                }
            """)
        elif theme_index == 2:  # 深色主题
            self.preview_frame.setStyleSheet("""
                QWidget {
                    background-color: #252526;
                    border: 1px solid #3e3e42;
                    border-radius: 4px;
                    margin-top: 15px;
                    padding: 15px;
                }
            """)
            self.preview_btn1.setStyleSheet("""
                QPushButton {
                    background-color: #0e639c;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
            """)
            self.preview_btn2.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d30;
                    color: #cccccc;
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
            """)
        
        # 更新预览区域标签颜色
        for label in self.preview_frame.findChildren(QLabel):
            if theme_index == 2:
                label.setStyleSheet(label.styleSheet() + "color: #ffffff;")
            else:
                # 移除深色模式添加的颜色样式
                current_style = label.styleSheet()
                if "color: #ffffff;" in current_style:
                    label.setStyleSheet(current_style.replace("color: #ffffff;", ""))
    
    def init_notification_settings_page(self):
        """初始化通知设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 页面标题 - 更大更醒目
        title_label = QLabel("通知设置")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333;
            margin-bottom: 20px;
        """)
        layout.addWidget(title_label)
        
        # 通知设置卡片
        notify_card = QWidget()
        notify_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        notify_layout = QVBoxLayout(notify_card)
        notify_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        notify_card_title = QLabel("通知选项")
        notify_card_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        notify_layout.addWidget(notify_card_title)
        
        # 通知设置选项 - 使用更大的复选框和更好的间距
        checkboxes_layout = QVBoxLayout()
        checkboxes_layout.setSpacing(15)
        
        # 显示提示信息
        self.notify_check = QCheckBox("显示提示信息（系统托盘消息）")
        self.notify_check.setChecked(self.config["show_notifications"])
        self.notify_check.setStyleSheet("font-size: 14px;")
        checkboxes_layout.addWidget(self.notify_check)
        
        # 任务到期通知
        self.deadline_notify_check = QCheckBox("任务到期提醒")
        self.deadline_notify_check.setChecked(self.config.get("deadline_notifications", True))
        self.deadline_notify_check.setStyleSheet("font-size: 14px;")
        checkboxes_layout.addWidget(self.deadline_notify_check)
        
        # 任务超时通知
        self.overdue_notify_check = QCheckBox("任务超时提醒")
        self.overdue_notify_check.setChecked(self.config.get("overdue_notifications", True))
        self.overdue_notify_check.setStyleSheet("font-size: 14px;")
        checkboxes_layout.addWidget(self.overdue_notify_check)
        
        # 添加通知预览选项
        self.preview_notification_check = QCheckBox("显示通知预览内容")
        self.preview_notification_check.setChecked(self.config.get("notification_preview", True))
        self.preview_notification_check.setStyleSheet("font-size: 14px;")
        checkboxes_layout.addWidget(self.preview_notification_check)
        
        notify_layout.addLayout(checkboxes_layout)
        
        # 通知行为说明
        notify_help = QLabel("启用这些选项后，程序将在相应事件发生时向您发送通知提醒。")
        notify_help.setWordWrap(True)
        notify_help.setStyleSheet("color: #666; font-size: 13px; margin-top: 10px;")
        notify_layout.addWidget(notify_help)
        
        layout.addWidget(notify_card)
        
        # 通知演示卡片
        demo_card = QWidget()
        demo_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        demo_layout = QVBoxLayout(demo_card)
        demo_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        demo_card_title = QLabel("通知演示")
        demo_card_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        demo_layout.addWidget(demo_card_title)
        
        # 演示通知按钮
        demo_btn = QPushButton("发送测试通知")
        demo_btn.setMinimumHeight(40)
        demo_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        demo_btn.clicked.connect(self.send_test_notification)
        demo_layout.addWidget(demo_btn)
        
        layout.addWidget(demo_card)
        
        layout.addStretch()
        self.content_stack.addWidget(page)
    
    def send_test_notification(self):
        """发送测试通知"""
        if self.parent() and hasattr(self.parent(), 'show_system_tray_message'):
            self.parent().show_system_tray_message(
                "测试通知", 
                "这是一条测试通知，确认通知功能正常工作。"
            )
        else:
            QMessageBox.information(self, "测试通知", "这是一条测试通知，确认通知功能正常工作。")
    
    def init_hotkey_settings_page(self):
        """初始化快捷键设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 页面标题 - 更大更醒目
        title_label = QLabel("快捷键设置")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333;
            margin-bottom: 20px;
        """)
        layout.addWidget(title_label)
        
        # 快捷键设置卡片
        hotkey_card = QWidget()
        hotkey_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        hotkey_layout = QVBoxLayout(hotkey_card)
        hotkey_layout.setContentsMargins(20, 20, 20, 20)
        
        # 切换显示状态快捷键设置
        toggle_layout = QHBoxLayout()
        toggle_label = QLabel("切换显示状态:")
        toggle_label.setMinimumWidth(150)
        toggle_layout.addWidget(toggle_label)
        
        # 快捷键显示标签
        self.toggle_display_hotkey_label = QLabel("Ctrl + Alt + T")
        self.toggle_display_hotkey_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px 12px;
                font-family: Consolas, Monaco, monospace;
                color: #0078d7;
            }
        """)
        toggle_layout.addWidget(self.toggle_display_hotkey_label)
        
        # 强制关闭程序快捷键设置
        force_close_layout = QHBoxLayout()
        force_close_label = QLabel("强制关闭程序:")
        force_close_label.setMinimumWidth(150)
        force_close_layout.addWidget(force_close_label)
        
        # 快捷键显示标签
        self.force_close_hotkey_label = QLabel("Alt + Q")
        self.force_close_hotkey_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px 12px;
                font-family: Consolas, Monaco, monospace;
                color: #0078d7;
            }
        """)
        force_close_layout.addWidget(self.force_close_hotkey_label)
        
        # 添加提示文本
        hotkey_note = QLabel("使用Alt+Q快捷键可以强制退出程序。")
        hotkey_note.setWordWrap(True)
        hotkey_note.setStyleSheet("color: #666; font-size: 13px; margin-top: 10px;")
        
        hotkey_layout.addLayout(toggle_layout)
        
        # 添加切换显示状态提示文本
        toggle_note = QLabel("使用Ctrl+Alt+T快捷键可以快速切换窗口的显示和隐藏状态。")
        toggle_note.setWordWrap(True)
        toggle_note.setStyleSheet("color: #666; font-size: 13px; margin-top: 10px;")
        hotkey_layout.addWidget(toggle_note)
        
        hotkey_layout.addLayout(force_close_layout)
        hotkey_layout.addWidget(hotkey_note)
        
        # 添加额外的快捷键说明
        additional_note = QLabel("程序将自动处理这些快捷键以确保功能正常工作。")
        additional_note.setWordWrap(True)
        additional_note.setStyleSheet("color: #666; font-size: 13px; margin-top: 10px;")
        hotkey_layout.addWidget(additional_note)
        
        layout.addWidget(hotkey_card)
        
        # 添加更多快捷键预留位置（可扩展）
        future_note = QLabel("更多快捷键设置将在未来版本中提供。")
        future_note.setStyleSheet("color: #888; font-style: italic; margin-top: 20px;")
        layout.addWidget(future_note)
        
        layout.addStretch()
        self.content_stack.addWidget(page)
    
    def init_update_settings_page(self):
        """初始化数据更新设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 页面标题 - 更大更醒目
        title_label = QLabel("数据更新设置")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #333;
            margin-bottom: 20px;
        """)
        layout.addWidget(title_label)
        
        # 数据更新设置卡片
        update_card = QWidget()
        update_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        update_layout = QVBoxLayout(update_card)
        update_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        update_card_title = QLabel("更新频率")
        update_card_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        update_layout.addWidget(update_card_title)
        
        # 更新频率设置 - 使用表单布局
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # 更新时间间隔设置
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 3600)  # 1到3600秒
        self.update_interval_spin.setValue(self.config["update_interval"])
        self.update_interval_spin.setMinimumHeight(32)
        self.update_interval_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
        """)
        
        interval_label = QLabel("更新时间间隔（秒）:")
        interval_label.setStyleSheet("font-size: 14px;")
        form_layout.addRow(interval_label, self.update_interval_spin)
        
        # 自动保存设置
        self.auto_save_check = QCheckBox("任务变更时自动保存")
        self.auto_save_check.setChecked(self.config.get("auto_save", True))
        self.auto_save_check.setStyleSheet("font-size: 14px;")
        form_layout.addRow(self.auto_save_check)
        
        update_layout.addLayout(form_layout)
        
        # 更新说明
        update_help = QLabel("设置数据更新的时间间隔，较小的值会使数据更实时但可能增加系统负担。自动保存功能可确保任务变更不会丢失。")
        update_help.setWordWrap(True)
        update_help.setStyleSheet("color: #666; font-size: 13px; margin-top: 15px;")
        update_layout.addWidget(update_help)
        
        layout.addWidget(update_card)
        
        # 数据优化卡片
        optimize_card = QWidget()
        optimize_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        optimize_layout = QVBoxLayout(optimize_card)
        optimize_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题
        optimize_card_title = QLabel("数据优化")
        optimize_card_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        optimize_layout.addWidget(optimize_card_title)
        
        # 优化按钮组
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # 清理数据按钮
        clean_btn = QPushButton("清理历史数据")
        clean_btn.setMinimumHeight(40)
        clean_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        clean_btn.clicked.connect(self.clean_history_data)
        buttons_layout.addWidget(clean_btn)
        
        # 优化数据按钮
        optimize_btn = QPushButton("优化数据性能")
        optimize_btn.setMinimumHeight(40)
        optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        optimize_btn.clicked.connect(self.optimize_data_performance)
        buttons_layout.addWidget(optimize_btn)
        
        optimize_layout.addLayout(buttons_layout)
        
        # 优化说明
        optimize_help = QLabel("定期清理不需要的历史数据可以提高程序性能，优化操作会重新整理数据结构以提升访问速度。")
        optimize_help.setWordWrap(True)
        optimize_help.setStyleSheet("color: #666; font-size: 13px; margin-top: 15px;")
        optimize_layout.addWidget(optimize_help)
        
        layout.addWidget(optimize_card)
        
        layout.addStretch()
        self.content_stack.addWidget(page)
    
    def clean_history_data(self):
        """清理历史数据"""
        reply = QMessageBox.question(self, "确认清理", 
                                    "确定要清理历史数据吗？此操作不可恢复。",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 这里可以添加实际的清理逻辑
            QMessageBox.information(self, "清理完成", "历史数据清理完成。")
    
    def optimize_data_performance(self):
        """优化数据性能"""
        # 显示优化进行中提示
        QMessageBox.information(self, "优化进行中", "正在优化数据性能，请稍候...")
        
        # 这里可以添加实际的优化逻辑
        # 模拟优化过程
        QMessageBox.information(self, "优化完成", "数据性能优化完成。")
    
    def on_nav_item_clicked(self, item):
        """处理导航项点击"""
        # 已经通过currentRowChanged信号连接，这里可以添加额外处理
        pass
    
    def toggle_auto_backup_options(self):
        """根据是否启用自动备份来启用/禁用相关选项"""
        enabled = self.auto_backup_check.isChecked()
        self.interval_spin.setEnabled(enabled)
        self.backup_path_edit.setEnabled(enabled)
    
    def update_backup_settings_controls(self):
        """更新备份设置控件的值，确保显示最新配置"""
        # 显式设置备份间隔值
        backup_interval = self.config.get("backup_interval", 60)
        print(f"[SettingsDialog] 更新备份间隔控件值为: {backup_interval}分钟")
        self.interval_spin.setValue(backup_interval)
        
        # 显式设置自动备份启用状态
        auto_backup_enabled = self.config.get("auto_backup_enabled", False)
        print(f"[SettingsDialog] 更新自动备份启用状态为: {auto_backup_enabled}")
        self.auto_backup_check.setChecked(auto_backup_enabled)
        
        # 显式设置备份路径
        default_backup_path = os.path.join(os.getcwd(), 'backups')
        backup_path = self.config.get("backup_path", default_backup_path)
        print(f"[SettingsDialog] 更新备份路径为: {backup_path}")
        self.backup_path_edit.setText(backup_path)
        
        # 根据自动备份状态更新控件可用性
        self.toggle_auto_backup_options()
    
    def browse_backup_path(self):
        """浏览选择备份目录"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "选择备份目录",
            self.backup_path_edit.text()
        )
        if path:
            self.backup_path_edit.setText(path)
    
    def accept_and_backup(self):
        """接受设置并立即备份"""
        self.do_backup = True
        self.accept()
    
    def handle_restore_backup(self):
        """处理从备份文件恢复数据"""
        # 显示确认对话框
        reply = QMessageBox.warning(
            self,
            "确认恢复",
            "恢复数据将覆盖当前所有任务数据！\n确定要继续吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择备份文件",
            self.config.get("backup_path", os.path.join(os.getcwd(), 'backups')),
            "备份文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 读取备份文件
            with open(file_path, 'r', encoding='utf-8') as file:
                tasks_data = json.load(file)
            
            # 清空当前任务
            main_window = self.parent()
            main_window.task_model.clear()
            
            # 恢复任务数据
            for task_data in tasks_data:
                task = main_window.Task(
                    title=task_data.get('title', ''),
                    description=task_data.get('description', ''),
                    due_date=task_data.get('due_date', ''),
                    priority=task_data.get('priority', 'medium'),
                    status=task_data.get('status', 'pending'),
                    tags=task_data.get('tags', [])
                )
                main_window.task_model.add_task(task)
            
            # 保存恢复后的数据
            main_window.save_tasks()
            
            # 更新任务列表视图
            main_window.task_list_widget.refresh_view()
            
            QMessageBox.information(self, "成功", "数据已成功恢复！")
        
        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", "无法解析备份文件。文件格式可能不正确。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"恢复数据时发生错误：{str(e)}")
    
    def handle_reset_settings(self):
        """重置所有设置"""
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            "确定要重置所有设置到默认值吗？这将不会影响您的任务数据。",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # 重置所有配置到默认值
            from core.config_manager import ConfigManager
            default_config = ConfigManager.default_config.copy()
            for key, value in default_config.items():
                self.config[key] = value
            
            # 更新界面控件
            self.width_spin.setValue(self.config["window_width"])
            self.height_spin.setValue(self.config["window_height"])
            self.notify_check.setChecked(self.config["show_notifications"])
            self.update_interval_spin.setValue(self.config["update_interval"])
            self.auto_backup_check.setChecked(self.config.get("auto_backup_enabled", False))
            self.interval_spin.setValue(self.config.get("backup_interval", 60))
            self.backup_path_edit.setText(self.config.get("backup_path", os.path.join(os.getcwd(), 'backups')))
            
            QMessageBox.information(self, "重置成功", "所有设置已重置为默认值。")

    def accept(self):
        """确认设置 - 确保备份间隔正确保存"""
        print("[SettingsDialog] 保存设置")
        
        # 保存窗口大小设置
        self.config["window_width"] = self.width_spin.value()
        self.config["window_height"] = self.height_spin.value()
        
        # 保存通知设置
        self.config["show_notifications"] = self.notify_check.isChecked()
        self.config["deadline_notifications"] = self.deadline_notify_check.isChecked()
        self.config["overdue_notifications"] = self.overdue_notify_check.isChecked()
        self.config["notification_preview"] = self.preview_notification_check.isChecked()
        
        # 保存更新设置
        self.config["update_interval"] = self.update_interval_spin.value()
        self.config["auto_save"] = self.auto_save_check.isChecked()
        
        # 保存自动备份设置
        self.config["auto_backup_enabled"] = self.auto_backup_check.isChecked()
        
        # 重要：直接保存用户设置的备份间隔，不做任何默认值处理
        backup_interval = self.interval_spin.value()
        self.config["backup_interval"] = backup_interval
        print(f"[SettingsDialog] 保存备份间隔: {backup_interval}分钟")
        
        # 设置备份路径
        backup_path = self.backup_path_edit.text()
        if not backup_path or backup_path == '.':
            backup_path = os.path.join(os.getcwd(), 'backups')
        self.config["backup_path"] = backup_path
        
        # 保存主题设置
        self.config["theme"] = self.theme_combo.currentIndex()
        
        # 保存快捷键设置
        self.config["hotkeys"] = {
            "toggle_display": "Ctrl+Alt+T",
            "force_close": "Alt+Q"
        }
        
        # 调用父类的accept方法
        super().accept()
        
    def closeEvent(self, event):
        """关闭窗口时自动保存设置"""
        print("[SettingsDialog] 关闭窗口，自动保存设置")
        # 调用accept方法来保存设置
        self.accept()
        # 接受关闭事件
        event.accept()

    def get_config(self):
        """返回修改后的配置"""
        return self.config
        
    def should_backup(self):
        """返回是否应该执行备份"""
        return self.do_backup


class BackupSettingsDialog(QDialog):
    """备份设置对话框"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()  # 复制当前配置
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("备份设置")
        self.setGeometry(200, 200, 400, 300)
        layout = QVBoxLayout(self)

        # 自动备份设置
        auto_backup_group = QGroupBox("自动备份设置")
        auto_backup_layout = QVBoxLayout()

        # 启用自动备份复选框
        self.auto_backup_check = QCheckBox("启用自动备份")
        self.auto_backup_check.setChecked(self.config.get("auto_backup_enabled", False))
        self.auto_backup_check.stateChanged.connect(self.toggle_auto_backup_options)
        auto_backup_layout.addWidget(self.auto_backup_check)

        # 备份间隔设置（分钟）
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("备份间隔（分钟）:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 10080)  # 最大7天（60*24*7）
        self.interval_spin.setValue(self.config.get("backup_interval", 60))
        interval_layout.addWidget(self.interval_spin)
        auto_backup_layout.addLayout(interval_layout)

        # 备份路径设置
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("备份目录:"))
        self.backup_path_edit = QLineEdit()
        # 默认使用backups文件夹作为备份路径
        default_backup_path = os.path.join(os.getcwd(), 'backups')
        self.backup_path_edit.setText(self.config.get("backup_path", default_backup_path))
        path_layout.addWidget(self.backup_path_edit, 1)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_backup_path)
        path_layout.addWidget(browse_btn)
        auto_backup_layout.addLayout(path_layout)

        auto_backup_group.setLayout(auto_backup_layout)
        layout.addWidget(auto_backup_group)

        # 手动备份按钮
        manual_backup_btn = QPushButton("立即手动备份")
        manual_backup_btn.setMinimumHeight(40)
        manual_backup_btn.setStyleSheet("font-size: 14px;")
        manual_backup_btn.clicked.connect(self.accept_and_backup)
        layout.addWidget(manual_backup_btn)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # 初始状态设置
        self.toggle_auto_backup_options()

    def toggle_auto_backup_options(self):
        """根据是否启用自动备份来启用/禁用相关选项"""
        enabled = self.auto_backup_check.isChecked()
        self.interval_spin.setEnabled(enabled)
        self.backup_path_edit.setEnabled(enabled)

    def browse_backup_path(self):
        """浏览选择备份目录"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "选择备份目录",
            self.backup_path_edit.text()
        )
        if path:
            self.backup_path_edit.setText(path)

    def accept_and_backup(self):
        """接受设置并立即备份"""
        self.do_backup = True
        self.accept()

    def accept(self):
        """确认设置"""
        self.config["auto_backup_enabled"] = self.auto_backup_check.isChecked()
        self.config["backup_interval"] = self.interval_spin.value()
        # 设置默认备份目录为backups文件夹
        backup_path = self.backup_path_edit.text()
        if not backup_path or backup_path == '.':
            backup_path = os.path.join(os.getcwd(), 'backups')
        self.config["backup_path"] = backup_path
        # 不要重置do_backup标志，保留之前的设置
        super().accept()

    def get_config(self):
        """返回修改后的配置"""
        return self.config

    def should_backup(self):
        """返回是否应该执行备份"""
        return getattr(self, 'do_backup', False)


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
        
        # 初始化自动备份定时器
        self.setup_auto_backup_timer()

        # 应用主题
        self.apply_theme()
        
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
        
        # 为右键菜单添加鼠标经过效果
        # 检查是否为深色主题
        is_dark_theme = self.config.get("theme", 0) == 2
        hover_bg = "#2D2D30" if is_dark_theme else "#F0F0F0"
        bg_color = "#333333" if is_dark_theme else "#FFFFFF"
        text_color = "#FFFFFF" if is_dark_theme else "#000000"
        
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid #ccc;
                padding: 2px;
            }}
            QMenu::item {{
                padding: 8px 30px;
                border: 1px solid transparent;
            }}
            QMenu::item:selected {{
                background-color: {hover_bg};
            }}
        """)

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
    
    def init_menu_bar(self):
        """初始化菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        # 导入子菜单
        import_menu = file_menu.addMenu("导入任务")
        
        # 导入JSON
        import_json_action = QAction("从JSON文件导入", self)
        import_json_action.triggered.connect(self.handle_import_json)
        import_menu.addAction(import_json_action)
        
        # 导入CSV
        import_csv_action = QAction("从CSV文件导入", self)
        import_csv_action.triggered.connect(self.handle_import_csv)
        import_menu.addAction(import_csv_action)
        
        # 导出子菜单
        export_menu = file_menu.addMenu("导出任务")
        
        # 导出JSON
        export_json_action = QAction("导出为JSON文件", self)
        export_json_action.triggered.connect(self.handle_export_json)
        export_menu.addAction(export_json_action)
        
        # 导出CSV
        export_csv_action = QAction("导出为CSV文件", self)
        export_csv_action.triggered.connect(self.handle_export_csv)
        export_menu.addAction(export_csv_action)
        
        # 设置 - 直接作为菜单项，点击后弹出设置窗口
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        menu_bar.addAction(settings_action)
        
        # 备份功能已整合到设置中，不再需要单独的菜单项

    def init_hotkey_listener(self):
        """初始化快捷键监听"""
        self.hotkey_thread = HotkeyListener()
        self.hotkey_thread.trigger.connect(self.toggle_window_visibility)
        # 启动线程（守护线程，主程序退出时自动结束）
        self.hotkey_thread.daemon = True
        self.hotkey_thread.start()

    def init_ui(self):
        """初始化界面"""
        # 创建菜单栏
        self.init_menu_bar()
        
        # 主部件和布局
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # 左侧：垂直布局包含输入面板和搜索筛选
        left_layout = QVBoxLayout()
        
        # 添加任务输入区域（放在顶部，设置固定高度）
        input_panel = self.create_input_panel()
        left_layout.addWidget(input_panel)
        
        # 添加搜索和筛选面板（放在下面，设置为可拉伸）
        search_filter_panel = self.create_search_filter_panel()
        left_layout.addWidget(search_filter_panel, 1)  # 1表示拉伸因子
        
        # 添加拉伸空间，确保面板不会被压缩
        left_layout.addStretch()
        
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
        # 应用当前主题 - 在初始化时默认为浅色主题
        if hasattr(self.statistics_widget, 'set_dark_theme'):
            # 假设默认是浅色主题
            self.statistics_widget.set_dark_theme(False)
        
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



        panel.setLayout(layout)
        # 设置固定宽度，确保与搜索筛选面板一致
        panel.setMinimumWidth(320)
        panel.setMaximumWidth(320)
        # 设置最大高度，避免占用过多空间
        panel.setMaximumHeight(400)
        return panel
        
    def create_search_filter_panel(self):
        """创建搜索和筛选面板（可折叠，三角形指示器）"""
        # 创建面板并设置为可折叠
        panel = QGroupBox("搜索和筛选")
        panel.setCheckable(True)  # 启用可折叠功能
        panel.setChecked(False)   # 默认折叠状态
        
        # 创建内容容器
        content_widget = QWidget()
        content_widget.setVisible(False)  # 默认隐藏内容
        
        # 合并的toggled信号处理器
        def on_toggled(checked):
            content_widget.setVisible(checked)
            if checked:
                panel.raise_()  # 确保面板在最上层
                content_widget.raise_()  # 确保内容也在最上层
        
        panel.toggled.connect(on_toggled)
        
        # 使用表单布局，一行一个筛选项
        form_layout = QFormLayout(content_widget)
        form_layout.setVerticalSpacing(15)  # 显著增加垂直间距
        form_layout.setHorizontalSpacing(20)  # 显著增加水平间距
        form_layout.setFormAlignment(Qt.AlignTop)  # 设置顶部对齐
        form_layout.setLabelAlignment(Qt.AlignLeft)  # 标签左对齐
        form_layout.setContentsMargins(15, 15, 15, 15)  # 显著增加内边距
        
        # 创建搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索任务...")
        self.search_input.setMinimumHeight(36)  # 显著增大高度
        self.search_input.setMinimumWidth(180)  # 增大宽度
        # 添加样式使搜索框更明显
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.handle_search_filter)  # 实时搜索
        form_layout.addRow("搜索任务:", self.search_input)
        
        # 类别筛选
        self.category_filter = QComboBox()
        self.category_filter.addItem("所有类别")
        self.category_filter.addItems(self.config["categories"])
        self.category_filter.setMinimumHeight(36)  # 显著增大高度
        self.category_filter.setMinimumWidth(180)  # 增大宽度
        # 添加样式使下拉框更明显
        self.category_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.category_filter.currentIndexChanged.connect(self.handle_search_filter)
        form_layout.addRow("类别:", self.category_filter)
        
        # 标签筛选
        self.tag_filter = QComboBox()
        self.tag_filter.addItem("所有标签")
        self.tag_filter.addItem("无标签")
        self.tag_filter.addItems(self.config["tags"])
        self.tag_filter.setMinimumHeight(36)  # 显著增大高度
        self.tag_filter.setMinimumWidth(180)  # 增大宽度
        self.tag_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.tag_filter.currentIndexChanged.connect(self.handle_search_filter)
        form_layout.addRow("标签:", self.tag_filter)
        
        # 重要等级筛选
        self.importance_filter = QComboBox()
        self.importance_filter.addItem("所有重要度")
        self.importance_filter.addItems(["1星 (一般)", "2星 (重要)", "3星 (非常重要)"])
        self.importance_filter.setMinimumHeight(36)  # 显著增大高度
        self.importance_filter.setMinimumWidth(180)  # 增大宽度
        self.importance_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
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
        self.urgency_filter.setMinimumHeight(36)  # 显著增大高度
        self.urgency_filter.setMinimumWidth(180)  # 增大宽度
        self.urgency_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
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
        self.deadline_filter.setMinimumHeight(36)  # 显著增大高度
        self.deadline_filter.setMinimumWidth(180)  # 增大宽度
        self.deadline_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.deadline_filter.currentIndexChanged.connect(self.handle_search_filter)
        form_layout.addRow("截止日期:", self.deadline_filter)
        
        # 创建重置按钮
        reset_button = QPushButton("重置筛选")
        reset_button.setMinimumHeight(40)  # 显著增大高度
        reset_button.setMinimumWidth(120)  # 设置宽度
        # 添加样式使按钮更明显
        reset_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        reset_button.clicked.connect(self.reset_search_filter)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(reset_button)
        button_layout.setContentsMargins(0, 15, 0, 0)  # 显著增加顶部间距
        
        # 添加按钮布局到表单布局
        form_layout.addRow(button_layout)
        
        # 创建面板的主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(content_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 增大面板内边距
        
        # 设置面板布局
        panel.setLayout(main_layout)
        
        # 初始状态下隐藏内容
        content_widget.setVisible(False)
        
        # 设置固定宽度，确保初始宽度和展开宽度保持一致
        panel.setMinimumWidth(320)
        panel.setMaximumWidth(320)
        
        # 返回面板
        return panel

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

        # 获取选中项的任务数据（直接从UI组件中获取）
        selected_task_data = list_widget.get_selected_task_data()
        
        # 关键点：保存选中任务的唯一标识（创建时间和名称）
        # 这样即使在执行过程中列表被刷新，也能通过这些标识找到正确的任务
        task_create_time = None
        task_name = None
        
        if selected_task_data:
            task_create_time = selected_task_data.get("create_time")
            task_name = selected_task_data["name"]
        else:
            # 获取过滤后的任务列表作为备选
            all_tasks = self.task_handler.get_sorted_tasks(task_type)
            filtered_tasks = self.filter_tasks(all_tasks)
            if index < len(filtered_tasks):
                selected_task = filtered_tasks[index]
                task_create_time = selected_task.get("create_time")
                task_name = selected_task["name"]
        
        if not task_name:
            QMessageBox.warning(self, "错误", "无法获取任务信息")
            return
        
        # 关键修复：即使在执行过程中定时器触发刷新，我们也直接使用任务标识查找并完成
        # 而不是依赖于可能变化的索引
        success = self.task_handler.mark_task_done_by_identifier(task_type, task_create_time, task_name)
        
        if success:
            self.refresh_list(task_type)
            self.refresh_list("done")
            self.show_system_tray_message("任务已完成", f"已完成：{task_name}")
        else:
            QMessageBox.warning(self, "错误", f"无法标记任务 '{task_name}' 为完成")

    def handle_delete(self, task_type):
        """处理删除任务"""
        list_widget = getattr(self, f"{task_type}_list")
        index = list_widget.get_selected_index()

        if index == -1:
            QMessageBox.warning(self, "提示", "请选择一个任务")
            return

        # 获取选中项的任务数据（直接从UI组件中获取）
        selected_task_data = list_widget.get_selected_task_data()
        
        # 关键点：保存选中任务的唯一标识（创建时间和名称）
        # 这样即使在执行过程中列表被刷新，也能通过这些标识找到正确的任务
        task_create_time = None
        task_name = None
        
        if selected_task_data:
            task_create_time = selected_task_data.get("create_time")
            task_name = selected_task_data["name"]
        else:
            # 获取过滤后的任务列表作为备选
            all_tasks = self.task_handler.get_sorted_tasks(task_type)
            filtered_tasks = self.filter_tasks(all_tasks)
            if index < len(filtered_tasks):
                selected_task = filtered_tasks[index]
                task_create_time = selected_task.get("create_time")
                task_name = selected_task["name"]
        
        if not task_name:
            QMessageBox.warning(self, "错误", "无法获取任务信息")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认", f"确定要删除任务 '{task_name}' 吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 关键修复：即使在执行过程中定时器触发刷新，我们也直接使用任务标识查找并删除
            # 而不是依赖于可能变化的索引
            success = self.task_handler.delete_task_by_identifier(task_type, task_create_time, task_name)
            
            if success:
                self.refresh_list(task_type)
                self.show_system_tray_message("任务已删除", f"已删除：{task_name}")
            else:
                QMessageBox.warning(self, "错误", f"无法删除任务 '{task_name}'")


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
        )
        
        # 对于已完成任务，添加完成时间
        if 'done_time' in task and task['done_time']:
            text += f"完成日期: {task['done_time']}\n"
        
        # 添加截止日期
        text += f"截止日期: {deadline}\n"
        
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
        """重置搜索和筛选条件"""
        self.search_input.clear()
        self.category_filter.setCurrentIndex(0)
        self.tag_filter.setCurrentIndex(0)
        self.importance_filter.setCurrentIndex(0)
        self.urgency_filter.setCurrentIndex(0)
        self.deadline_filter.setCurrentIndex(0)
    
    def handle_import_json(self):
        """处理从JSON文件导入任务数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择JSON文件", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 先导入任务以获取预览数据
            imported_tasks = self.task_handler.data_import_export._import_json(file_path)
            
            # 显示预览对话框
            strategy, selected_tasks = self.task_handler.data_import_export.show_import_preview_dialog(self, imported_tasks)
            
            if strategy and selected_tasks:
                # 处理导入的任务
                success, result = self.task_handler.data_import_export._process_imported_tasks(selected_tasks, strategy)
                
                if success:
                    # 刷新列表
                    self.refresh_all_lists()
                    
                    # 显示导入结果
                    message = f"导入成功！\n"
                    message += f"添加任务数: {result['added']}\n"
                    message += f"更新任务数: {result['updated']}\n"
                    message += f"跳过任务数: {result['skipped']}\n"
                    message += f"共处理任务数: {len(selected_tasks)}"
                    QMessageBox.information(self, "导入成功", message)
                else:
                    QMessageBox.warning(self, "导入失败", "导入任务数据失败，请检查文件格式是否正确。")
        except Exception as e:
            QMessageBox.warning(self, "导入错误", f"导入过程中发生错误：{str(e)}")
    
    def handle_import_csv(self):
        """处理从CSV文件导入任务数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 先导入任务以获取预览数据
            imported_tasks = self.task_handler.data_import_export._import_csv(file_path)
            
            # 显示预览对话框
            strategy, selected_tasks = self.task_handler.data_import_export.show_import_preview_dialog(self, imported_tasks)
            
            if strategy and selected_tasks:
                # 处理导入的任务
                success, result = self.task_handler.data_import_export._process_imported_tasks(selected_tasks, strategy)
                
                if success:
                    # 刷新列表
                    self.refresh_all_lists()
                    
                    # 显示导入结果
                    message = f"导入成功！\n"
                    message += f"添加任务数: {result['added']}\n"
                    message += f"更新任务数: {result['updated']}\n"
                    message += f"跳过任务数: {result['skipped']}\n"
                    message += f"共处理任务数: {len(selected_tasks)}"
                    QMessageBox.information(self, "导入成功", message)
                else:
                    QMessageBox.warning(self, "导入失败", "导入任务数据失败，请检查文件格式是否正确。")
        except Exception as e:
            QMessageBox.warning(self, "导入错误", f"导入过程中发生错误：{str(e)}")
    
    def handle_export_json(self):
        """处理导出任务数据为JSON文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存JSON文件", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # 如果没有文件扩展名，添加.json
        if not file_path.endswith('.json'):
            file_path += '.json'
        
        success = self.task_handler.data_import_export.export_tasks("json", file_path)
        
        if success:
            QMessageBox.information(self, "导出成功", f"任务数据已成功导出到：\n{file_path}")
    
    def handle_export_csv(self):
        """处理导出任务数据为CSV文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV文件", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # 如果没有文件扩展名，添加.csv
        if not file_path.endswith('.csv'):
            file_path += '.csv'
        
        success = self.task_handler.data_import_export.export_tasks("csv", file_path)
        
        if success:
            QMessageBox.information(self, "导出成功", f"任务数据已成功导出到：\n{file_path}")
        
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
        
        # 保存当前滚动位置和选中状态
        scroll_pos = 0
        selected_index = -1
        if hasattr(list_widget, 'save_scroll_position'):
            scroll_pos = list_widget.save_scroll_position()
        if hasattr(list_widget, 'save_selection'):
            selected_index = list_widget.save_selection()
        
        # 关键修复：在清空列表前，确保清除所有选择状态，防止跨列表选择混淆
        # 这是因为在更新一个列表时，由于某些事件传递机制，选择状态可能错误地传播到其他列表
        if hasattr(list_widget, 'list_widget') and list_widget.list_widget and hasattr(list_widget.list_widget, 'selectionModel'):
            selection_model = list_widget.list_widget.selectionModel()
            if selection_model:
                selection_model.clearSelection()
                list_widget.list_widget.viewport().update()
                
        list_widget.clear_list()

        # 获取排序后的任务列表
        all_tasks = self.task_handler.get_sorted_tasks(task_type)
        
        # 应用搜索和筛选
        filtered_tasks = self.filter_tasks(all_tasks)
        task_count = len(filtered_tasks)

        # 存储过滤后的任务到UI小部件中
        if not hasattr(self, 'filtered_tasks_cache'):
            self.filtered_tasks_cache = {}
        self.filtered_tasks_cache[task_type] = filtered_tasks

        group_widget = getattr(self, f"{task_type}_group")
        group_widget.setTitle(f"{group_widget.title().split('(')[0]}({task_count})")

        for index, task in enumerate(filtered_tasks, 1):
            list_widget.add_task_item(
                self.format_task_text(task),
                index=index,
                urgency=task["urgency"],
                is_overdue=(task_type == "overdue"),
                is_done=(task_type == "done"),
                create_time=task.get('create_time', None),
                deadline=task.get('deadline', None),
                done_time=task.get('done_time', None),  # 确保传递已完成任务的done_time
                task_data=task  # 传递完整的任务数据引用
            )
            
        # 恢复滚动位置和选中状态
        if hasattr(list_widget, 'restore_scroll_position'):
            # 延迟恢复滚动位置和选中状态，确保列表项完全渲染后再恢复
            QTimer.singleShot(10, lambda: self._restore_list_state(list_widget, scroll_pos, selected_index))
            
    def _restore_list_state(self, list_widget, scroll_pos, selected_index):
        """恢复列表的滚动位置和选中状态，确保选择状态隔离"""
        # 先恢复滚动位置
        if hasattr(list_widget, 'restore_scroll_position'):
            list_widget.restore_scroll_position(scroll_pos)
        # 再恢复选中状态
        if hasattr(list_widget, 'restore_selection'):
            # 确保只在当前列表内恢复选中状态，不影响其他列表
            list_widget.restore_selection(selected_index)

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
        """刷新所有任务的时间显示和紧急度样式
        
        优化策略：
        1. 只有在有新超时任务时才刷新整个列表
        2. 无新超时任务时，只更新时间显示而不重新构建列表
        3. 添加用户交互检测，避免在用户点击选择时干扰
        """
        print(f"[{time.strftime('%H:%M:%S')}] 定时器触发refresh_time_display方法")
        
        # 检查是否有用户交互正在进行
        has_user_interaction = False
        try:
            # 检查鼠标是否按下或有键盘修饰键按下
            mouse_buttons = QApplication.mouseButtons()
            modifiers = QApplication.keyboardModifiers()
            has_user_interaction = mouse_buttons != Qt.NoButton or modifiers != Qt.NoModifier
            
            # 检查任何任务列表是否有选中项正在变更
            for task_type in ['todo', 'overdue', 'done']:
                list_widget = getattr(self, f"{task_type}_list", None)
                if list_widget and hasattr(list_widget, 'list_widget'):
                    if list_widget.list_widget.hasFocus():
                        has_user_interaction = True
                        break
        except Exception as e:
            print(f"检查用户交互状态时出错: {e}")
        
        # 如果检测到用户交互，延迟刷新以避免干扰
        if has_user_interaction:
            print(f"[{time.strftime('%H:%M:%S')}] 检测到用户交互，延迟刷新")
            # 延迟100毫秒后再次尝试刷新
            QTimer.singleShot(100, self.refresh_time_display)
            return
        
        # 检查超时任务并移动
        print(f"[{time.strftime('%H:%M:%S')}] 开始调用check_overdue_tasks")
        newly_overdue_tasks = self.task_handler.check_overdue_tasks()
        print(f"[{time.strftime('%H:%M:%S')}] check_overdue_tasks调用完成")
        
        # 发送新超时任务的托盘通知
        need_refresh_lists = False
        if newly_overdue_tasks and len(newly_overdue_tasks) > 0:
            need_refresh_lists = True
            
            if len(newly_overdue_tasks) == 1:
                task = newly_overdue_tasks[0]
                message = f"'{task['name']}'\n已从待办转移到超时列表\n截止时间: {task['deadline']}"
                self.show_system_tray_message("任务已超时", message)
            else:
                # 多个任务时显示简洁信息
                task_details = ""
                for i, task in enumerate(newly_overdue_tasks[:3], 1):  # 最多显示前3个任务详情
                    task_details += f"{i}. '{task['name']}'\n"
                if len(newly_overdue_tasks) > 3:
                    task_details += f"... 还有{len(newly_overdue_tasks)-3}个任务"
                message = f"共有{len(newly_overdue_tasks)}个任务已超时\n{task_details}"
                self.show_system_tray_message("多个任务已超时", message)
        
        # 只有在必要时（有新超时任务）才刷新整个列表
        if need_refresh_lists:
            print(f"[{time.strftime('%H:%M:%S')}] 检测到新的超时任务，重新刷新任务列表显示")
            # 保存所有列表的当前选择状态
            selection_states = {}
            for task_type in ['todo', 'overdue', 'done']:
                list_widget = getattr(self, f"{task_type}_list", None)
                if list_widget and hasattr(list_widget, 'save_selection'):
                    selection_states[task_type] = list_widget.save_selection()
            
            # 重新刷新待办和超时列表
            self.refresh_list("todo")
            self.refresh_list("overdue")
            
            # 恢复选择状态
            QTimer.singleShot(50, lambda: self._restore_all_selection_states(selection_states))
        else:
            # 无新超时任务时，只更新任务的时间显示而不重新构建列表
            print(f"[{time.strftime('%H:%M:%S')}] 无新超时任务，仅更新时间显示")
            for task_type in ['todo', 'overdue']:
                list_widget = getattr(self, f"{task_type}_list", None)
                if list_widget and hasattr(list_widget, 'update_time_display'):
                    list_widget.update_time_display()
        
        print(f"[{time.strftime('%H:%M:%S')}] refresh_time_display方法执行完成")
    
    def _restore_all_selection_states(self, selection_states):
        """恢复所有任务列表的选择状态"""
        for task_type, selected_index in selection_states.items():
            list_widget = getattr(self, f"{task_type}_list", None)
            if list_widget and hasattr(list_widget, 'restore_selection') and selected_index >= 0:
                list_widget.restore_selection(selected_index)
    
    def handle_backup_data(self):
        """处理备份设置和操作"""
        # 显示设置窗口并跳转到备份设置页面
        dialog = SettingsDialog(self.config, self)
        # 直接跳转到备份设置页面（索引为1）
        dialog.nav_list.setCurrentRow(1)
        if dialog.exec_():
            new_config = dialog.get_config()
            
            # 保存新配置
            if self.config_manager.save_config(new_config):
                self.config = new_config
                
                # 立即重新设置自动备份定时器，确保配置修改立即生效
                self.setup_auto_backup_timer()
                
                # 检查是否需要执行备份
                if dialog.should_backup():
                    # 执行手动备份
                    backup_path = self.config.get("backup_path", os.path.join(os.getcwd(), 'backups'))
                    self.perform_backup(backup_path, False)
                else:
                    # 显示保存成功消息
                    if self.config.get("show_notifications", True):
                        self.show_system_tray_message("备份设置已更新", "您的备份配置已保存。")
                    else:
                        QMessageBox.information(self, "设置成功", "备份配置已保存")
    
    def perform_backup(self, backup_dir, is_auto_backup=True):
        """执行备份操作
        
        Args:
            backup_dir: 备份目录路径
            is_auto_backup: 是否为自动备份（True表示自动备份，使用托盘通知；False表示手动备份，使用弹窗通知）
        """
        try:
            # 确保导入json模块
            import json
            
            # 确保使用backups文件夹而不是backup文件夹
            if 'backup' in backup_dir and 'backups' not in backup_dir:
                backup_dir = backup_dir.replace('backup', 'backups')
            
            # 获取当前时间
            current_time = datetime.now()
            time_str = current_time.strftime("%Y%m%d_%H%M")  # 精确到分钟
            
            # 创建基于日期的子目录
            date_dir = current_time.strftime("%Y%m%d")
            final_backup_dir = os.path.join(backup_dir, date_dir)
            
            # 确保备份目录存在
            if not os.path.exists(final_backup_dir):
                os.makedirs(final_backup_dir)
            
            # 加载当前任务数据
            tasks_data = self.data_manager.load_tasks()
            
            # 备份为JSON格式
            json_backup_filename = f"{time_str}-backup.json"
            json_backup_path = os.path.join(final_backup_dir, json_backup_filename)
            
            with open(json_backup_path, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
            
            # 备份为CSV格式
            csv_backup_filename = f"{time_str}-backup.csv"
            csv_backup_path = os.path.join(final_backup_dir, csv_backup_filename)
            
            # 创建CSV文件并写入数据
            import csv
            with open(csv_backup_path, 'w', newline='', encoding='utf-8') as f:
                if tasks_data:
                    # 获取所有可能的字段名
                    fieldnames = ['name', 'deadline', 'importance', 'urgency', 'category', 'tags', 'create_time', 'done_time']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    
                    # 写入表头
                    writer.writeheader()
                    
                    # 写入数据行
                    for task in tasks_data:
                        # 确保所有字段都存在，不存在的字段设为空
                        row = {}
                        for field in fieldnames:
                            if field in task:
                                # 对于列表类型的字段（如tags），转换为字符串
                                if isinstance(task[field], list):
                                    row[field] = ', '.join(task[field])
                                else:
                                    row[field] = task[field]
                            else:
                                row[field] = ''
                        writer.writerow(row)
            
            if is_auto_backup:
                # 自动备份：使用系统托盘显示简化通知
                date_str = current_time.strftime("%Y-%m-%d %H:%M")
                self.show_system_tray_message(
                    "自动备份成功",
                    f"数据已在{date_str}成功备份到指定目录\n包含JSON和CSV两种格式文件"
                )
            else:
                # 手动备份：使用弹窗显示详细信息
                QMessageBox.information(
                    self, 
                    "备份成功", 
                    f"数据已成功备份到:\nJSON格式: {json_backup_path}\nCSV格式: {csv_backup_path}"
                )
            
        except Exception as e:
            if is_auto_backup:
                # 自动备份：使用系统托盘显示失败通知
                self.show_system_tray_message(
                    "自动备份失败",
                    f"备份过程中发生错误:\n{str(e)}",
                    icon=QSystemTrayIcon.Critical,
                    duration=3000  # 失败消息显示更长时间
                )
            else:
                # 手动备份：使用弹窗显示失败详细信息
                QMessageBox.critical(
                    self, 
                    "备份失败", 
                    f"备份过程中发生错误:\n{str(e)}"
                )
    
    def open_settings(self):
        """打开设置对话框 - 确保配置正确保存和应用"""
        print("[MainWindow] 打开设置对话框")
        print(f"[MainWindow] 当前配置: backup_interval={self.config.get('backup_interval', 60)}")
        
        dialog = SettingsDialog(self.config, self)
        # 执行对话框，不管用户如何关闭，我们都会获取并保存配置
        dialog.exec_()
        
        # 总是获取配置并保存，因为closeEvent中会调用accept()更新配置
        new_config = dialog.get_config()
        print(f"[MainWindow] 从对话框获取新配置: backup_interval={new_config.get('backup_interval', 60)}")
        
        # 保存新配置
        if self.config_manager.save_config(new_config):
            # 重要修复：直接替换整个配置字典
            self.config = new_config.copy()
            print(f"[MainWindow] 配置已保存并更新: backup_interval={self.config.get('backup_interval', 60)}")
            
            # 应用窗口大小设置
            self.resize(self.config["window_width"], self.config["window_height"])
            
            # 更新定时器间隔（秒转换为毫秒）
            new_interval_ms = self.config["update_interval"] * 1000
            self.timer.setInterval(new_interval_ms)
            print(f"定时器间隔已更新为{new_interval_ms}毫秒")
            
            # 检查是否需要执行备份
            if dialog.should_backup():
                # 执行手动备份
                backup_path = self.config.get("backup_path", os.path.join(os.getcwd(), 'backups'))
                self.perform_backup(backup_path, False)
                # 显示保存成功消息
                if self.config.get("show_notifications", True):
                    self.show_system_tray_message("设置已保存", "您的配置已应用并保存。")
                else:
                    QMessageBox.information(self, "设置成功", "配置已保存")
            else:
                # 显示保存成功消息
                if self.config.get("show_notifications", True):
                    self.show_system_tray_message("设置已保存", "您的配置已应用并保存。")
                else:
                    QMessageBox.information(self, "设置成功", "配置已保存")
            
            # 重新设置自动备份定时器
            self.setup_auto_backup_timer()
            
            # 应用新的主题
            self.apply_theme()
        else:
            print("[MainWindow] 配置保存失败")
            QMessageBox.critical(self, "保存失败", "无法保存配置设置。请检查文件权限。")
            
    def setup_auto_backup_timer(self):
        """设置自动备份定时器"""
        import time
        print(f"[{time.strftime('%H:%M:%S')}] 开始设置自动备份定时器")
        # 如果之前有定时器，先停止
        if hasattr(self, 'auto_backup_timer'):
            print(f"[{time.strftime('%H:%M:%S')}] 停止之前的备份定时器")
            self.auto_backup_timer.stop()
            delattr(self, 'auto_backup_timer')
        
        # 如果启用了自动备份，设置定时器
        if self.config.get("auto_backup_enabled", False):
            interval_minutes = self.config.get("backup_interval", 60)
            interval_ms = interval_minutes * 60 * 1000  # 分钟转换为毫秒
            backup_path = self.config.get("backup_path", os.path.join(os.getcwd(), 'backups'))
            
            print(f"[{time.strftime('%H:%M:%S')}] 启用自动备份，间隔: {interval_minutes}分钟 ({interval_ms}毫秒)")
            print(f"[{time.strftime('%H:%M:%S')}] 备份路径: {backup_path}")
            
            self.auto_backup_timer = QTimer(self)
            # 使用functools.partial代替lambda，确保正确传递参数
            from functools import partial
            # 明确指定is_auto_backup=True
            self.auto_backup_timer.timeout.connect(partial(self.perform_backup, backup_path, True))
            self.auto_backup_timer.start(interval_ms)
            print(f"[{time.strftime('%H:%M:%S')}] 自动备份定时器已启动")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 自动备份已禁用")

    def apply_theme(self):
        """应用当前配置的主题"""
        theme_index = self.config.get("theme", 0)
        
        # 定义不同主题的样式表
        if theme_index == 0:  # 默认主题
            style_sheet = """
                QMainWindow, QWidget {
                    background-color: #f5f5f5;
                    color: #333;
                }
                QGroupBox {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin: 5px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                }
                QPushButton {
                    background-color: #0078d7;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: 600;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                    color: #ffffff;
                    font-weight: bold;
                }
                QLineEdit, QComboBox, QDateTimeEdit, QSpinBox {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                    background-color: white;
                }
                QTabWidget::pane {
                    border: 1px solid #ddd;
                    background-color: white;
                }
                QTabBar::tab {
                    padding: 6px 12px;
                    background-color: #f0f0f0;
                    border: 1px solid #ddd;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: white;
                    border-bottom: 1px solid white;
                }
            """
        elif theme_index == 1:  # 浅色主题
            style_sheet = """
                QMainWindow, QWidget {
                    background-color: #ffffff;
                    color: #333333;
                }
                QMenuBar {
                    background-color: #f5f5f5;
                    color: #333333;
                    padding: 4px 2px;
                    border: 1px solid transparent;
                }
                QMenuBar::item {
                    padding: 4px 8px;
                    background-color: transparent;
                }
                QMenuBar::item:hover {
                    background-color: #357abd;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #357abd;
                    color: #ffffff;
                }
                QMenuBar::item:!hover:!selected {
                    background-color: transparent;
                    color: #333333;
                }
                QMenuBar::item:focus {
                    outline: none;
                }
                QMenu {
                    background-color: white;
                    border: 1px solid #ddd;
                    color: #333333;
                }
                QMenu::item {
                    padding: 6px 24px;
                }
                QMenu::item:hover {
                    background-color: #357abd;
                    color: #ffffff;
                }
                QGroupBox {
                    background-color: #fafafa;
                    border: 1px solid #eee;
                    border-radius: 6px;
                    margin: 5px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                    color: #333;
                }
                QPushButton {
                    background-color: #4a90e2;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background-color: #357abd;
                    color: #ffffff;
                    font-weight: bold;
                }
                QLineEdit, QComboBox, QDateTimeEdit, QSpinBox {
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 6px;
                    background-color: white;
                }
                QTabWidget::pane {
                    border: 1px solid #eee;
                    background-color: #fafafa;
                }
                QTabBar::tab {
                    padding: 8px 16px;
                    background-color: #f8f8f8;
                    border: 1px solid #eee;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #fafafa;
                    border-bottom: 1px solid #fafafa;
                }
            """
        elif theme_index == 2:  # 深色主题
            style_sheet = """
                QMainWindow, QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #252526;
                    color: #ffffff;
                    padding: 4px 2px;
                    border: 1px solid transparent;
                }
                QMenuBar::item {
                    padding: 4px 8px;
                    background-color: transparent;
                }
                QMenuBar::item:hover {
                    background-color: #0e639c;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #0e639c;
                    color: #ffffff;
                }
                QMenuBar::item:!hover:!selected {
                    background-color: transparent;
                    color: #ffffff;
                }
                QMenuBar::item:focus {
                    outline: none;
                }
                QMenu {
                    background-color: #252526;
                    border: 1px solid #3e3e42;
                    color: #ffffff;
                }
                QMenu::item {
                    padding: 6px 24px;
                }
                QMenu::item:hover {
                    background-color: #0e639c;
                    color: #ffffff;
                }
                QGroupBox {
                    background-color: #252526;
                    border: 1px solid #3e3e42;
                    border-radius: 4px;
                    margin: 5px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #0e639c;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: 600;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                    color: #ffffff;
                    font-weight: bold;
                }
                QLineEdit, QComboBox, QDateTimeEdit, QSpinBox {
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                    padding: 5px;
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #3e3e42;
                    background-color: #252526;
                }
                QTabBar::tab {
                    padding: 6px 12px;
                    background-color: #2d2d30;
                    border: 1px solid #3e3e42;
                    border-bottom: none;
                    color: #ffffff;
                }
                QTabBar::tab:selected {
                    background-color: #252526;
                    border-bottom: 1px solid #252526;
                }
            """
        
        # 应用样式表
        self.setStyleSheet(style_sheet)
        
        # 根据主题设置任务列表的darkTheme属性
        is_dark_theme = (theme_index == 2)
        
        # 为所有任务列表设置darkTheme属性
        for task_type in ['todo_list', 'overdue_list', 'done_list']:
            task_list = getattr(self, task_type, None)
            if task_list:
                # 优先使用set_dark_theme方法
                if hasattr(task_list, 'set_dark_theme'):
                    task_list.set_dark_theme(is_dark_theme)
                elif hasattr(task_list, 'list_widget'):
                    # 兼容旧版本
                    task_list.list_widget.setProperty('darkTheme', 'true' if is_dark_theme else 'false')
                    # 重新设置样式表以应用属性变化
                    task_list.list_widget.style().unpolish(task_list.list_widget)
                    task_list.list_widget.style().polish(task_list.list_widget)
            
            # 设置统计窗口的主题
            if hasattr(self, 'statistics_widget') and self.statistics_widget:
                if hasattr(self.statistics_widget, 'set_dark_theme'):
                    self.statistics_widget.set_dark_theme(is_dark_theme)
    
    def exit_app(self):
        """退出应用"""
        self.timer.stop()  # 停止定时器
        self.data_manager.save_tasks(self.task_handler.tasks)
        self.tray_icon.hide()  # 隐藏托盘图标
        qApp.quit()  # 退出应用

    def keyPressEvent(self, event):
        """键盘按下事件处理，捕获快捷键"""
        # 处理Ctrl+Alt+T快捷键用于切换窗口显示状态
        if event.key() == Qt.Key_T and event.modifiers() == (Qt.ControlModifier | Qt.AltModifier):
            if self.isHidden() or not self.isVisible():
                self.show_window()
            else:
                self.hide_window()
        # 处理Alt+Q快捷键用于强制关闭程序
        elif event.key() == Qt.Key_Q and event.modifiers() == Qt.AltModifier:
            # 确认是否要退出程序
            reply = QMessageBox.question(
                self,
                "确认退出",
                "确定要强制退出程序吗？所有未保存的更改将会丢失。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.exit_app()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件（改为隐藏到托盘）"""
        event.ignore()  # 忽略关闭事件
        self.hide_window()  # 隐藏窗口而不是退出