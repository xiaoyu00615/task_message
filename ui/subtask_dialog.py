from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QListWidget, 
                             QListWidgetItem, QPushButton, QLineEdit, QMessageBox, QInputDialog,
                             QCheckBox, QSplitter, QFrame, QGroupBox, QHeaderView, QTableWidget,
                             QTableWidgetItem, QScrollArea, QDateEdit, QTimeEdit, QWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette
from datetime import datetime
from copy import deepcopy


class SubTaskDialog(QDialog):
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        # 确保task_data是字典类型
        if not isinstance(task_data, dict):
            self.task_data = {}
        else:
            # 深度复制任务数据避免引用问题
            from copy import deepcopy
            self.task_data = deepcopy(task_data)
            # 确保必要的字段存在
            if 'subtasks' not in self.task_data:
                self.task_data['subtasks'] = []
        self.is_dark_theme = False
        self.init_ui()
        self.load_task_data()
        
    def _get_task_item_text(self, item):
        """从任务项中获取文本内容（统一处理，减少重复代码）"""
        try:
            # 优先从UserRole获取
            data = item.data(Qt.UserRole)
            if isinstance(data, dict):
                return data.get('text', '').strip()
            
            # 如果UserRole中没有，尝试从widget获取
            widget = self.subtask_list.itemWidget(item)
            if widget:
                for label in widget.findChildren(QLabel):
                    # 去除HTML标签获取纯文本
                    plain_text = label.text().replace('<s>', '').replace('</s>', '')
                    if plain_text.strip():
                        return plain_text.strip()
        except Exception as e:
            print(f"[WARNING] 获取任务文本时出错: {str(e)}")
        
        return ""
    
    def _safe_attribute_get(self, obj, attr_name, default_value=None, attr_type=None):
        """安全地获取对象属性，提供类型检查和默认值
        
        参数:
            obj: 要获取属性的对象
            attr_name: 属性名称
            default_value: 默认值
            attr_type: 可选，期望的属性类型
            
        返回:
            属性值（如果存在且类型正确）或默认值
        """
        try:
            if hasattr(obj, attr_name):
                value = getattr(obj, attr_name)
                if attr_type is None or isinstance(value, attr_type):
                    return value
                else:
                    print(f"[WARNING] 属性 {attr_name} 类型错误，期望 {attr_type.__name__}，实际 {type(value).__name__}")
        except Exception as e:
            print(f"[ERROR] 获取属性 {attr_name} 时出错: {str(e)}")
        return default_value
    
    def _update_last_modified(self):
        """更新最后修改时间（统一处理，减少重复代码）"""
        try:
            if hasattr(self, 'task_data') and isinstance(self.task_data, dict):
                from datetime import datetime
                self.task_data['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return True
        except Exception as e:
            print(f"[ERROR] 更新最后修改时间时出错: {str(e)}")
        return False
    
    def _validate_subtask_data(self, subtask):
        """验证并标准化单个任务项数据
        
        参数:
            subtask: 任务项数据
            
        返回:
            (is_valid, message, validated_text) 元组
        """
        if isinstance(subtask, dict):
            # 确保必要字段存在
            if 'text' not in subtask:
                subtask['text'] = ''
            if 'completed' not in subtask:
                subtask['completed'] = False
            # 验证文本不为空
            text = subtask.get('text', '').strip()
            if not text:
                return False, "任务内容不能为空", ""
            return True, "验证成功", text
        elif isinstance(subtask, str):
            text = subtask.strip()
            if text:
                return True, "验证成功", text
        return False, "无效的任务数据", ""
        
    def init_ui(self):
        # 设置窗口标题和大小
        # 从任务数据中获取任务名称，如果没有则使用默认值
        task_name = self.task_data.get('name', '未命名任务')
        self.setWindowTitle(f"任务详情 - {task_name}")
        self.setMinimumSize(700, 600)
        
        # 设置焦点策略和键盘导航支持
        self.setFocusPolicy(Qt.StrongFocus)
        # 设置窗口为活动窗口时自动聚焦到第一个输入控件
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # 任务标题
        title_label = QLabel("任务名称")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title_label)
        
        self.title_edit = QLineEdit()
        self.title_edit.setStyleSheet("padding: 8px; font-size: 14px;")
        main_layout.addWidget(self.title_edit)
        
        # 截止时间
        deadline_layout = QHBoxLayout()
        deadline_label = QLabel("截止时间")
        deadline_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        deadline_layout.addWidget(deadline_label)
        
        self.deadline_date = QDateEdit()
        self.deadline_date.setCalendarPopup(True)
        self.deadline_date.setDisplayFormat("yyyy-MM-dd")
        deadline_layout.addWidget(self.deadline_date)
        
        self.deadline_time = QTimeEdit()
        self.deadline_time.setDisplayFormat("HH:mm")
        deadline_layout.addWidget(self.deadline_time)
        
        main_layout.addLayout(deadline_layout)
        
        # 使用分割器分隔不同部分
        splitter = QSplitter(Qt.Vertical)
        
        # 左侧：内容描述区域
        content_group = QGroupBox("内容描述")
        content_layout = QVBoxLayout(content_group)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("请输入任务的详细描述...")
        self.description_edit.setMinimumHeight(150)
        content_layout.addWidget(self.description_edit)
        
        # 右侧：细碎任务区域
        subtask_group = QGroupBox("细碎任务项")
        subtask_layout = QVBoxLayout(subtask_group)
        
        # 细碎任务输入和添加按钮
        input_layout = QHBoxLayout()
        self.subtask_input = QLineEdit()
        self.subtask_input.setPlaceholderText("输入细碎任务...")
        input_layout.addWidget(self.subtask_input, 3)
        
        self.add_subtask_btn = QPushButton("添加")
        self.add_subtask_btn.clicked.connect(self.add_subtask)
        input_layout.addWidget(self.add_subtask_btn, 1)
        
        subtask_layout.addLayout(input_layout)
        
        # 细碎任务列表
        self.subtask_list = QListWidget()
        self.subtask_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 2px 0;
                border-radius: 3px;
            }
        """)
        
        # 为细碎任务列表的项添加右键菜单支持
        self.subtask_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.subtask_list.customContextMenuRequested.connect(self.show_subtask_context_menu)
        
        # 增强任务列表的可访问性
        self.subtask_list.setFocusPolicy(Qt.StrongFocus)
        self.subtask_list.setSelectionMode(QListWidget.SingleSelection)  # 单选模式
        self.subtask_list.setAccessibleName("任务列表")
        self.subtask_list.setAccessibleDescription("显示所有细碎任务，可通过键盘导航和操作")
        
        # 连接任务列表的键盘事件
        self.subtask_list.keyPressEvent = self.on_subtask_list_key_press
        
        subtask_layout.addWidget(self.subtask_list)
        
        # 细碎任务统计
        self.stats_label = QLabel("完成: 0 / 总计: 0")
        subtask_layout.addWidget(self.stats_label, alignment=Qt.AlignRight)
        
        # 将两个区域添加到分割器
        splitter.addWidget(content_group)
        splitter.addWidget(subtask_group)
        # 设置分割器的初始大小
        splitter.setSizes([200, 300])
        
        main_layout.addWidget(splitter, 1)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.ok_btn = QPushButton("确定 (&O)")  # 添加Alt+O快捷键
        self.ok_btn.setObjectName("ok_btn")
        self.ok_btn.setMinimumHeight(36)
        self.ok_btn.setDefault(True)  # 设置为默认按钮，按Enter键自动触发
        self.ok_btn.setFocusPolicy(Qt.StrongFocus)
        self.ok_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("取消 (&C)")  # 添加Alt+C快捷键
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.setFocusPolicy(Qt.StrongFocus)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        
        main_layout.addLayout(btn_layout)
        
        # 设置深色主题支持
        self.set_dark_theme_support()
        
        # 设置焦点顺序
        self.setTabOrder(self.title_edit, self.deadline_date)
        self.setTabOrder(self.deadline_date, self.deadline_time)
        self.setTabOrder(self.deadline_time, self.description_edit)
        self.setTabOrder(self.description_edit, self.subtask_input)
        self.setTabOrder(self.subtask_input, self.add_subtask_btn)
        self.setTabOrder(self.add_subtask_btn, self.subtask_list)
        self.setTabOrder(self.subtask_list, self.cancel_btn)
        self.setTabOrder(self.cancel_btn, self.ok_btn)
    
    def set_dark_theme_support(self):
        # 检测父级主题设置
        parent = self.parent()
        if parent and hasattr(parent, 'config'):
            theme_index = parent.config.get("theme", 0)
        else:
            theme_index = 0  # 默认主题
        
        # 创建主题样式
        default_theme = """
            QDialog {
                background-color: #f0f0f0;
                color: #000000;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                background-color: #ffffff;
                color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                top: -7px;
                padding: 0 5px 0 5px;
                background-color: #ffffff;
                color: #000000;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit, QTextEdit, QDateEdit, QTimeEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                background-color: #e6e6e6;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #d9d9d9;
            }
            QPushButton#ok_btn {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
            }
            QPushButton#ok_btn:hover {
                background-color: #1177bb;
            }
            QListWidget {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QListWidget::item {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e6f2ff;
                color: #000000;
            }
        """
        
        light_theme = """
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                background-color: #ffffff;
                color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                top: -7px;
                padding: 0 5px 0 5px;
                background-color: #ffffff;
                color: #000000;
            }
            QLabel {
                color: #555555;
            }
            QLineEdit, QTextEdit, QDateEdit, QTimeEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                background-color: #f5f5f5;
                color: #333333;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e9e9e9;
            }
            QPushButton#ok_btn {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
            }
            QPushButton#ok_btn:hover {
                background-color: #1177bb;
            }
            QListWidget {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
            }
            QListWidget::item {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #e6f2ff;
                color: #000000;
            }
        """
        
        dark_theme = """
            QDialog {
                background-color: #252526;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #3e3e42;
                border-radius: 5px;
                margin-top: 10px;
                background-color: #2d2d30;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                top: -7px;
                padding: 0 5px 0 5px;
                background-color: #2d2d30;
                color: #ffffff;
            }
            QLabel {
                color: #cccccc;
            }
            QLineEdit, QTextEdit, QDateEdit, QTimeEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton#cancel_btn {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #3e3e42;
            }
            QPushButton#cancel_btn:hover {
                background-color: #4c4c4c;
            }
            QListWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #3e3e42;
            }
            QListWidget::item {
                background-color: #2d2d30;
                color: #ffffff;
                border: 1px solid #3e3e42;
            }
            QListWidget::item:selected {
                background-color: #0e639c;
            }
        """
        
        # 应用相应主题
        if theme_index == 1:  # 浅色主题
            self.setStyleSheet(light_theme)
        elif theme_index == 2:  # 深色主题
            self.setStyleSheet(dark_theme)
        else:  # 默认主题
            self.setStyleSheet(default_theme)
    
    def load_task_data(self):
        """加载任务数据到界面，增强数据验证、错误处理和用户体验"""
        try:
            print("[INFO] 开始加载任务数据")
            
            # 确保task_data是字典类型
            if not isinstance(self.task_data, dict):
                print("[WARNING] 任务数据不是字典类型，已重置为空字典")
                self.task_data = {}
                
            # 深度复制任务数据避免引用问题
            from copy import deepcopy
            safe_task_data = deepcopy(self.task_data)
            
            # 确保subtasks字段存在且为列表
            if 'subtasks' not in safe_task_data or not isinstance(safe_task_data['subtasks'], list):
                safe_task_data['subtasks'] = []
                self.task_data['subtasks'] = []  # 同时更新原始数据
                print("[INFO] subtasks字段不存在或不是列表，已初始化为空列表")
                
            # 加载任务标题
            task_name = safe_task_data.get('name', '').strip()
            if not task_name:
                task_name = '未命名'
            print(f"[INFO] 加载任务名称: {task_name[:30]}...")
            
            try:
                self.title_edit.setText(task_name)
            except AttributeError:
                # 兼容旧版UI命名
                if hasattr(self, 'task_name_input'):
                    self.task_name_input.setText(task_name)
                else:
                    print("[WARNING] 未找到标题编辑组件")
            
            # 加载描述
            description = safe_task_data.get('description', '').strip()
            print(f"[INFO] 加载任务描述，长度: {len(description)} 字符")
            
            try:
                self.description_edit.setPlainText(description)
            except AttributeError:
                # 兼容旧版UI命名
                if hasattr(self, 'task_description_input'):
                    self.task_description_input.setText(description)
                else:
                    print("[WARNING] 未找到描述编辑组件")
            
            # 设置截止时间 - 支持多种字段名和格式
            deadline_str = None
            if 'deadline' in safe_task_data and safe_task_data['deadline']:
                deadline_str = safe_task_data['deadline']
            elif 'due_date' in safe_task_data and safe_task_data['due_date']:
                deadline_str = safe_task_data['due_date']
                print("[INFO] 使用due_date字段作为截止时间")
            
            if deadline_str:
                try:
                    from PyQt5.QtCore import QDate, QTime
                    
                    # 扩展的日期时间格式支持
                    date_formats = [
                        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", 
                        "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y",
                        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%fZ"
                    ]
                    
                    deadline_dt = None
                    for fmt in date_formats:
                        try:
                            deadline_dt = datetime.strptime(deadline_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if deadline_dt:
                        try:
                            # 尝试使用日期时间组件
                            self.deadline_date.setDate(QDate(deadline_dt.year, deadline_dt.month, deadline_dt.day))
                            self.deadline_time.setTime(QTime(deadline_dt.hour, deadline_dt.minute))
                            print(f"[INFO] 成功加载截止时间: {deadline_dt.strftime('%Y-%m-%d %H:%M')}")
                        except AttributeError:
                            # 兼容只有日期的组件
                            if hasattr(self, 'task_due_date'):
                                self.task_due_date.setDate(QDate(deadline_dt.year, deadline_dt.month, deadline_dt.day))
                                print(f"[INFO] 成功加载截止日期: {deadline_dt.strftime('%Y-%m-%d')}")
                    else:
                        print(f"[WARNING] 无法解析截止时间格式: {deadline_str}")
                        # 尝试简单的日期解析
                        try:
                            # 尝试只解析日期部分
                            if isinstance(deadline_str, str):
                                # 去除时间部分
                                if ' ' in deadline_str:
                                    date_part = deadline_str.split(' ')[0]
                                else:
                                    date_part = deadline_str
                                
                                # 尝试基本的日期格式
                                simple_formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
                                for simple_fmt in simple_formats:
                                    try:
                                        simple_dt = datetime.strptime(date_part, simple_fmt)
                                        # 设置日期
                                        if hasattr(self, 'deadline_date'):
                                            self.deadline_date.setDate(QDate(simple_dt.year, simple_dt.month, simple_dt.day))
                                        elif hasattr(self, 'task_due_date'):
                                            self.task_due_date.setDate(QDate(simple_dt.year, simple_dt.month, simple_dt.day))
                                        print(f"[INFO] 成功解析日期部分: {simple_dt.strftime('%Y-%m-%d')}")
                                        break
                                    except ValueError:
                                        continue
                        except Exception as parse_error:
                            print(f"[ERROR] 解析日期部分失败: {str(parse_error)}")
                except Exception as time_error:
                    print(f"[ERROR] 设置截止时间时出错: {str(time_error)}")
            
            # 加载优先级（如果存在）
            if hasattr(self, 'task_priority') and 'priority' in safe_task_data:
                priority = safe_task_data['priority']
                if priority in ["低", "中", "高"]:
                    try:
                        self.task_priority.setCurrentText(priority)
                        print(f"[INFO] 已加载优先级: {priority}")
                    except Exception as priority_error:
                        print(f"[WARNING] 设置优先级失败: {str(priority_error)}")
            
            # 加载任务状态（如果存在）
            if hasattr(self, 'task_status') and 'status' in safe_task_data:
                status = safe_task_data['status']
                if status in ["未开始", "进行中", "已完成", "暂停"]:
                    try:
                        self.task_status.setCurrentText(status)
                        print(f"[INFO] 已加载任务状态: {status}")
                    except Exception as status_error:
                        print(f"[WARNING] 设置任务状态失败: {str(status_error)}")
            
            # 加载细碎任务
            subtasks = safe_task_data.get('subtasks', [])
            print(f"[INFO] 准备加载细碎任务，数量: {len(subtasks)}")
            
            # 先清空列表，避免重复加载
            try:
                self.subtask_list.clear()
                print("[INFO] 细碎任务列表已清空")
            except Exception as clear_error:
                print(f"[ERROR] 清空任务列表失败: {str(clear_error)}")
                return
            
            # 确保subtasks是列表类型
            if not isinstance(subtasks, list):
                print(f"[WARNING] subtasks不是列表类型，转换为列表: {type(subtasks).__name__}")
                subtasks = [subtasks] if subtasks else []
            
            
            # 添加每个细碎任务 - 增强错误处理和数据验证
            loaded_count = 0
            skipped_count = 0
            error_count = 0
            
            for i, subtask in enumerate(subtasks):
                try:
                    # 处理不同格式的细碎任务数据
                    text = ""
                    completed = False
                    
                    if isinstance(subtask, dict):
                        text = subtask.get('text', '').strip()
                        completed = bool(subtask.get('completed', False))
                        # 可以在这里添加更多字段的处理，如创建时间、修改时间等
                    else:
                        # 兼容旧格式（字符串或其他类型）
                        try:
                            text = str(subtask).strip()
                            completed = False
                        except:
                            text = ""
                    
                    # 只添加非空任务
                    if text:
                        print(f"[INFO] 加载细碎任务 {i+1}: '{text[:30]}...', 完成状态: {completed}")
                        result = self.add_subtask_item(text, completed)
                        if result:
                            loaded_count += 1
                        else:
                            skipped_count += 1
                            print(f"[WARNING] 任务项 {i+1} 添加失败")
                    else:
                        skipped_count += 1
                        print(f"[WARNING] 跳过空的细碎任务: 索引 {i}")
                except Exception as e:
                    error_count += 1
                    print(f"[ERROR] 加载任务项 {i+1} 时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            print(f"[INFO] 任务加载统计: 成功 {loaded_count}, 跳过 {skipped_count}, 错误 {error_count}")
            
            # 确保至少有一个空任务（可选行为，可以根据需求调整）
            if loaded_count == 0:
                print("[INFO] 未加载到非空细碎任务，添加一个空任务项")
                # 注意：在优化后的add_subtask_item中，空任务会被过滤掉
                # 如果确实需要一个占位项，可以考虑添加一个特殊标记的任务
            
            # 更新统计
            try:
                self.update_subtask_stats()
                print("[INFO] 任务统计已更新")
            except Exception as stats_error:
                print(f"[ERROR] 更新任务统计失败: {str(stats_error)}")
                import traceback
                traceback.print_exc()
            
            print("[INFO] 任务数据加载完成")
            
        except Exception as e:
            print(f"[ERROR] load_task_data方法出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 显示用户友好的错误消息
            try:
                QMessageBox.warning(
                    self, 
                    "加载错误", 
                    "加载任务数据时发生错误，部分数据可能未正确加载。\n"
                    "请检查任务数据格式后重试。",
                    QMessageBox.Ok
                )
            except Exception as msg_error:
                print(f"[ERROR] 显示错误消息失败: {str(msg_error)}")
            # 出错时也确保至少有一个空任务项
            try:
                self.add_subtask_item("", False)
            except:
                pass
            # 尝试更新统计
            try:
                self.update_subtask_stats()
            except:
                pass
    
    def add_subtask(self):
        """添加新的细碎任务，增强数据验证和错误处理"""
        try:
            # 获取并清理输入文本
            text = self.subtask_input.text().strip()
            
            # 使用工具方法验证任务数据
            is_valid, message, validated_text = self._validate_subtask_data(text)
            if not is_valid:
                # 数据无效，清空输入框并返回
                self.subtask_input.clear()
                return
            
            print(f"[DEBUG] 添加细碎任务: {validated_text}")
            # 添加细碎任务项
            self.add_subtask_item(validated_text, False)
            
            # 清空输入框
            self.subtask_input.clear()
            
            # 更新统计信息
            self.update_subtask_stats()
            
            # 使用工具方法更新最后修改时间
            self._update_last_modified()
                
        except Exception as e:
            # 记录错误但不中断程序
            print(f"[ERROR] 添加细碎任务时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 清空输入框以允许用户重试
            self.subtask_input.clear()
    
    def add_subtask_item(self, text, completed=False, task_index=None):
        """添加一个细碎任务项到列表中，支持在指定位置插入
        
        Args:
            text (str): 任务文本内容
            completed (bool, optional): 是否已完成
            task_index (int, optional): 插入位置的索引，如果为None则添加到末尾
        
        Returns:
            QListWidgetItem: 创建的任务项，失败时返回None
        """
        try:
            # 输入验证
            if not text or not isinstance(text, str):
                print("[WARNING] 尝试添加空任务或非字符串任务")
                return None
            
            # 去除多余空白字符
            text = text.strip()
            if not text:
                print("[WARNING] 尝试添加只包含空白字符的任务")
                return None
            
            # 创建一个自定义的QListWidgetItem
            item = QListWidgetItem()
            
            # 创建一个包含按钮和标签的小部件
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(20)
            
            # 添加完成按钮
            complete_btn = QPushButton("完成" if not completed else "已完成")
            complete_btn.setFixedSize(80, 40)
            complete_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px;
                    border-radius: 6px;
                    background-color: #4CAF50;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 80px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                    font-size: 15px;
                }
                QPushButton:pressed {
                    background-color: #2E7D32;
                }
            """)
            # 存储任务完成状态
            complete_btn.setProperty("is_completed", completed)
            # 增强的数据存储
            complete_btn.setProperty("task_text", text)
            complete_btn.clicked.connect(lambda _, btn=complete_btn, t=text, l_item=item: self.toggle_subtask_completion(btn, t, l_item))
            layout.addWidget(complete_btn, alignment=Qt.AlignVCenter)
            
            # 任务文本标签
            label = QLabel(text)
            if completed:
                # 如果任务已完成，添加删除线
                label.setText(f"<s>{text}</s>")
            # 保存标签引用到按钮属性，方便后续更新
            complete_btn.setProperty("label", label)
            
            # 增强标签显示效果
            label.setWordWrap(True)
            label.setMinimumHeight(60)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setStyleSheet("""
                QLabel {
                    padding: 15px 10px;
                    color: #333333;
                    font-size: 16px;
                    font-weight: 700;
                    min-height: 60px;
                    max-height: 180px;
                    line-height: 1.6;
                    background-color: #ffffff;
                    border-radius: 6px;
                    border: 1px solid #e0e0e0;
                }
                QLabel:hover {
                    background-color: #fafafa;
                    border-color: #d0d0d0;
                }
            """)
            layout.addWidget(label, 1, alignment=Qt.AlignVCenter)
            
            # 编辑按钮
            edit_btn = QPushButton("编辑")
            edit_btn.setFixedSize(80, 40)
            edit_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px;
                    border-radius: 6px;
                    background-color: #2196F3;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 80px;
                    min-height: 40px;
                    margin-right: 5px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                    font-size: 15px;
                }
                QPushButton:pressed {
                    background-color: #1565C0;
                }
            """)
            edit_btn.clicked.connect(lambda _, i=item, t=text: self.edit_subtask(i, t))
            layout.addWidget(edit_btn, alignment=Qt.AlignVCenter)
            
            # 删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(80, 40)
            delete_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 16px;
                    border-radius: 6px;
                    background-color: #f44336;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 80px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                    font-size: 15px;
                }
                QPushButton:pressed {
                    background-color: #b71c1c;
                }
            """)
            delete_btn.clicked.connect(lambda _, i=item: self.delete_subtask(i))
            layout.addWidget(delete_btn, alignment=Qt.AlignVCenter)
            
            # 设置widget样式和尺寸
            widget.setMinimumHeight(100)
            widget.setMaximumHeight(200)
            widget.setStyleSheet("""
                QWidget {
                    background-color: #f9f9f9;
                    border-radius: 10px;
                    min-height: 100px;
                    max-height: 200px;
                    border: 2px solid #e0e0e0;
                }
                QWidget:hover {
                    background-color: #f0f0f0;
                    border-color: #d0d0d0;
                }
            """)
            
            # 设置widget上下文菜单 - 使用闭包保存当前项的引用
            widget.setContextMenuPolicy(Qt.CustomContextMenu)
            widget.customContextMenuRequested.connect(
                lambda point, i=item: self.show_subtask_context_menu(point, self.subtask_list.row(i))
            )
            
            # 获取当前时间
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 将增强的数据存储到item中
            task_data = {
                'text': text,
                'completed': completed,
                'create_time': current_time,
                'last_modified': current_time
            }
            item.setData(Qt.UserRole, task_data)
            
            # 设置项的大小
            item.setSizeHint(QSize(0, 120))
            
            # 根据索引决定插入位置
            if task_index is not None and isinstance(task_index, int):
                # 验证索引范围
                if 0 <= task_index <= self.subtask_list.count():
                    self.subtask_list.insertItem(task_index, item)
                    print(f"[INFO] 在索引 {task_index} 处插入任务: {text[:30]}...")
                else:
                    print(f"[WARNING] 索引 {task_index} 超出范围，添加到末尾")
                    self.subtask_list.addItem(item)
            else:
                self.subtask_list.addItem(item)
                print(f"[INFO] 添加新任务: {text[:30]}...")
            
            # 设置widget
            self.subtask_list.setItemWidget(item, widget)
            
            # 更新任务的最后修改时间
            if hasattr(self, 'task_data') and isinstance(self.task_data, dict):
                try:
                    self.task_data['last_modified'] = current_time
                except Exception as time_error:
                    print(f"[WARNING] 更新任务最后修改时间失败: {str(time_error)}")
            
            # 更新统计
            self.update_subtask_stats()
            
            print(f"[DEBUG] 细碎任务项创建成功: {text[:30]}..., 完成状态: {completed}")
            return item
            
        except Exception as e:
            print(f"[ERROR] 创建细碎任务项时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 确保即使出错也更新统计
            try:
                self.update_subtask_stats()
            except Exception as stats_error:
                print(f"[WARNING] 更新任务统计失败: {str(stats_error)}")
            return None
    
    def toggle_subtask_completion(self, button, text, item):
        """切换细碎任务的完成状态，增强错误处理和数据同步"""
        try:
            # 获取当前完成状态
            is_completed = not button.property("is_completed")
            button.setProperty("is_completed", is_completed)
            
            # 更新按钮文本和样式
            button.setText("已完成" if is_completed else "完成")
            
            # 获取标签并更新显示
            label = button.property("label")
            if label:
                if is_completed:
                    label.setText(f"<s>{text}</s>")
                else:
                    label.setText(text)
            
            # 更新item的数据
            if item:
                try:
                    # 获取并更新item的数据
                    data = item.data(Qt.UserRole)
                    if isinstance(data, dict):
                        data['completed'] = is_completed
                        item.setData(Qt.UserRole, data)
                except Exception as data_error:
                    print(f"[ERROR] 更新item数据时出错: {str(data_error)}")
            
            # 更新统计信息
            self.update_subtask_stats()
            
            # 使用工具方法更新最后修改时间
            self._update_last_modified()
                    
            print(f"[DEBUG] 切换任务状态: '{text}' -> {'已完成' if is_completed else '未完成'}")
            
        except Exception as e:
            print(f"[ERROR] 切换任务完成状态时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def edit_subtask(self, item, current_text):
        """编辑细碎任务，增强数据验证和错误处理"""
        try:
            # 验证输入参数
            if not item or not isinstance(current_text, str):
                print("[ERROR] 无效的编辑参数")
                return
            
            # 显示输入对话框编辑任务文本
            new_text, ok = QInputDialog.getText(self, "编辑任务", "修改任务内容:", text=current_text)
            
            # 验证新文本
            if ok:
                cleaned_text = new_text.strip()
                if not cleaned_text:
                    print("[WARNING] 任务文本不能为空，编辑取消")
                    return
                
                # 获取项对应的小部件
                widget = self.subtask_list.itemWidget(item)
                if not widget:
                    print("[ERROR] 无法获取任务项的小部件")
                    return
                
                # 更新标签文本和完成按钮属性
                label = None
                completed_status = False
                
                # 查找标签和完成按钮
                for child in widget.findChildren(QLabel):
                    label = child
                    break
                
                # 查找完成按钮并更新状态
                for btn in widget.findChildren(QPushButton):
                    if btn.text() in ["完成", "已完成"]:
                        try:
                            completed_status = btn.property("is_completed")
                            btn.setProperty("task_text", cleaned_text)
                            print(f"[DEBUG] 更新按钮属性: task_text={cleaned_text}, is_completed={completed_status}")
                        except Exception as btn_error:
                            print(f"[ERROR] 更新按钮属性时出错: {str(btn_error)}")
                        break
                
                # 更新标签显示
                if label:
                    if completed_status:
                        label.setText(f"<s>{cleaned_text}</s>")
                    else:
                        label.setText(cleaned_text)
                    print(f"[DEBUG] 更新标签文本: {cleaned_text}")
                
                # 更新item的数据（通过UserRole存储）
                try:
                    # 获取并更新item的数据
                    data = item.data(Qt.UserRole)
                    if isinstance(data, dict):
                        data['text'] = cleaned_text
                        # 保留原有的完成状态
                        data['completed'] = completed_status
                        item.setData(Qt.UserRole, data)
                        print(f"[DEBUG] 更新item数据: {data}")
                    else:
                        # 如果没有有效的数据结构，创建一个新的
                        new_data = {'text': cleaned_text, 'completed': completed_status}
                        item.setData(Qt.UserRole, new_data)
                        print(f"[DEBUG] 创建新的item数据: {new_data}")
                except Exception as data_error:
                    print(f"[ERROR] 更新item数据时出错: {str(data_error)}")
                
                # 使用工具方法更新最后修改时间
                self._update_last_modified()
                
                print(f"[INFO] 成功编辑细碎任务: '{cleaned_text}'")
        except Exception as e:
            print(f"[ERROR] 编辑细碎任务时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def delete_subtask(self, item):
        """删除细碎任务，增强错误处理和用户确认逻辑"""
        try:
            # 验证输入参数
            if not item:
                print("[ERROR] 无效的删除参数")
                return
            
            # 使用工具方法获取任务文本
            task_text = self._get_task_item_text(item)
            
            # 构建更具体的确认消息
            confirm_msg = '确定要删除这个细碎任务吗？'
            if task_text:
                # 限制显示的文本长度
                display_text = task_text[:30] + ('...' if len(task_text) > 30 else '')
                confirm_msg = f'确定要删除细碎任务 "{display_text}" 吗？'
            
            # 确认删除
            reply = QMessageBox.question(self, '确认删除', confirm_msg,
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 获取项的索引并删除
                index = self.subtask_list.row(item)
                if index >= 0:
                    # 记录删除前的统计信息用于验证
                    before_count = self.subtask_list.count()
                    
                    # 执行删除操作
                    self.subtask_list.takeItem(index)
                    
                    # 验证删除是否成功
                    after_count = self.subtask_list.count()
                    if after_count == before_count - 1:
                        print(f"[INFO] 成功删除细碎任务: {task_text}")
                        
                        # 更新统计信息
                        self.update_subtask_stats()
                        
                        # 使用工具方法更新最后修改时间
                        self._update_last_modified()
                    else:
                        print(f"[ERROR] 删除任务后数量不正确，预期减少1个，实际变化: {after_count - before_count}")
                else:
                    print(f"[ERROR] 无效的任务索引: {index}")
            else:
                print("[INFO] 用户取消删除操作")
        except Exception as e:
            print(f"[ERROR] 删除细碎任务时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 确保即使出错也更新统计
            try:
                self.update_subtask_stats()
            except:
                pass
    
    def keyPressEvent(self, event):
        """处理键盘事件，添加快捷键支持"""
        try:
            # Ctrl+S 保存数据
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
                success, message = self.save_task_data()
                if success:
                    QMessageBox.information(self, "保存成功", message)
                else:
                    QMessageBox.warning(self, "保存提示", message)
                return
            
            # Ctrl+N 在任务列表获得焦点时添加新任务
            elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_N and self.subtask_list.hasFocus():
                self.add_subtask_btn.click()
                return
            
            # Delete/Esc 在任务列表获得焦点时删除选中项
            elif (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.subtask_list.hasFocus():
                selected_items = self.subtask_list.selectedItems()
                if selected_items:
                    self.delete_subtask(selected_items[0])
                return
            
            # 调用父类的keyPressEvent以处理其他事件
            super().keyPressEvent(event)
            
        except Exception as e:
            print(f"[ERROR] 处理键盘事件时出错: {str(e)}")
            super().keyPressEvent(event)
    
    def on_subtask_list_key_press(self, event):
        """处理任务列表的键盘事件，增强键盘导航"""
        try:
            selected_items = self.subtask_list.selectedItems()
            if not selected_items:
                # 如果没有选中项，调用原始的keyPressEvent
                QListWidget.keyPressEvent(self.subtask_list, event)
                return
            
            current_item = selected_items[0]
            current_index = self.subtask_list.row(current_item)
            
            # 空格键切换任务完成状态
            if event.key() == Qt.Key_Space:
                self.on_toggle_completion_from_context(current_item)
                return
            
            # Enter键编辑任务
            elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                self.on_edit_subtask_from_context(current_item)
                return
            
            # Up/Down箭头导航
            elif event.key() == Qt.Key_Up and current_index > 0:
                next_item = self.subtask_list.item(current_index - 1)
                self.subtask_list.setCurrentItem(next_item)
                self.subtask_list.scrollToItem(next_item, QAbstractItemView.PositionAtCenter)
                return
            elif event.key() == Qt.Key_Down and current_index < self.subtask_list.count() - 1:
                next_item = self.subtask_list.item(current_index + 1)
                self.subtask_list.setCurrentItem(next_item)
                self.subtask_list.scrollToItem(next_item, QAbstractItemView.PositionAtCenter)
                return
            
            # F2键编辑任务
            elif event.key() == Qt.Key_F2:
                self.on_edit_subtask_from_context(current_item)
                return
            
            # 调用原始的keyPressEvent以处理其他事件
            QListWidget.keyPressEvent(self.subtask_list, event)
            
        except Exception as e:
            print(f"[ERROR] 处理任务列表键盘事件时出错: {str(e)}")
            # 出错时回退到原始行为
            QListWidget.keyPressEvent(self.subtask_list, event)
    
    def show_subtask_context_menu(self, position, item_index=None):
        """显示细碎任务的右键菜单，增强菜单功能和错误处理"""
        try:
            # 确定要操作的任务项
            item = None
            if item_index is not None and 0 <= item_index < self.subtask_list.count():
                # 如果提供了索引，使用索引获取项
                item = self.subtask_list.item(item_index)
            else:
                # 否则，尝试从位置获取项
                item = self.subtask_list.itemAt(position)
            
            if not item:
                # 如果没有选中任何项，不显示菜单
                return
            
            # 创建右键菜单
            menu = QMenu(self)
            
            # 添加编辑操作
            edit_action = menu.addAction("编辑任务")
            edit_action.triggered.connect(lambda: self.on_edit_subtask_from_context(item))
            
            # 添加完成/取消完成操作
            is_completed = False
            try:
                # 尝试从UserRole获取完成状态
                data = item.data(Qt.UserRole)
                if isinstance(data, dict):
                    is_completed = data.get('completed', False)
            except Exception as status_error:
                print(f"[WARNING] 获取任务完成状态时出错: {str(status_error)}")
            
            toggle_action = menu.addAction("取消完成" if is_completed else "标记为完成")
            toggle_action.triggered.connect(lambda: self.on_toggle_completion_from_context(item))
            
            # 添加分隔线
            menu.addSeparator()
            
            # 添加删除操作
            delete_action = menu.addAction("删除任务")
            delete_action.triggered.connect(lambda: self.delete_subtask(item))
            
            # 添加分隔线
            menu.addSeparator()
            
            # 添加移动操作
            move_up_action = menu.addAction("上移")
            move_up_action.triggered.connect(lambda: self.move_subtask_up(item))
            
            move_down_action = menu.addAction("下移")
            move_down_action.triggered.connect(lambda: self.move_subtask_down(item))
            
            # 根据任务位置禁用相应的移动操作
            current_index = self.subtask_list.row(item)
            move_up_action.setEnabled(current_index > 0)
            move_down_action.setEnabled(current_index < self.subtask_list.count() - 1)
            
            # 显示菜单
            menu.exec_(self.subtask_list.mapToGlobal(position))
            
        except Exception as e:
            print(f"[ERROR] 显示右键菜单时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def on_edit_subtask_from_context(self, item):
        """从右键菜单编辑任务"""
        try:
            # 获取任务文本
            task_text = ""
            try:
                # 尝试从UserRole获取
                data = item.data(Qt.UserRole)
                if isinstance(data, dict):
                    task_text = data.get('text', '')
                
                # 如果UserRole中没有，尝试从widget获取
                if not task_text:
                    widget = self.subtask_list.itemWidget(item)
                    if widget:
                        for label in widget.findChildren(QLabel):
                            # 去除HTML标签获取纯文本
                            plain_text = label.text().replace('<s>', '').replace('</s>', '')
                            if plain_text.strip():
                                task_text = plain_text.strip()
                                break
            except Exception as text_error:
                print(f"[WARNING] 从右键菜单获取任务文本时出错: {str(text_error)}")
            
            # 调用编辑方法
            self.edit_subtask(item, task_text)
            
        except Exception as e:
            print(f"[ERROR] 从右键菜单编辑任务时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def on_toggle_completion_from_context(self, item):
        """从右键菜单切换任务完成状态"""
        try:
            # 查找完成按钮并触发点击
            widget = self.subtask_list.itemWidget(item)
            if widget:
                for btn in widget.findChildren(QPushButton):
                    if btn.text() in ["完成", "已完成"]:
                        # 直接调用toggle_subtask_completion方法
                        try:
                            # 获取任务文本
                            task_text = ""
                            data = item.data(Qt.UserRole)
                            if isinstance(data, dict):
                                task_text = data.get('text', '')
                            
                            # 切换完成状态
                            self.toggle_subtask_completion(btn, task_text, item)
                            print("[INFO] 从右键菜单切换任务完成状态")
                        except Exception as toggle_error:
                            print(f"[ERROR] 切换完成状态时出错: {str(toggle_error)}")
                        break
            
        except Exception as e:
            print(f"[ERROR] 从右键菜单切换任务完成状态时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def move_subtask_up(self, item):
        """将任务项上移"""
        try:
            current_index = self.subtask_list.row(item)
            if current_index > 0:
                # 获取当前项的数据
                data = item.data(Qt.UserRole)
                
                # 移除当前项
                self.subtask_list.takeItem(current_index)
                
                # 在新位置插入
                self.subtask_list.insertItem(current_index - 1, item)
                
                # 重新设置widget（因为takeItem会移除widget）
                old_widget = self.subtask_list.itemWidget(item)  # 这里可能返回None，需要处理
                if old_widget:
                    self.subtask_list.setItemWidget(item, old_widget)
                
                print(f"[INFO] 任务上移: 从索引 {current_index} 到 {current_index - 1}")
                
                # 更新任务的最后修改时间
                if hasattr(self, 'task_data') and isinstance(self.task_data, dict):
                    try:
                        self.task_data['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as time_error:
                        print(f"[WARNING] 更新最后修改时间失败: {str(time_error)}")
        except Exception as e:
            print(f"[ERROR] 移动任务上移时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def move_subtask_down(self, item):
        """将任务项下移"""
        try:
            current_index = self.subtask_list.row(item)
            if current_index < self.subtask_list.count() - 1:
                # 获取当前项的数据
                data = item.data(Qt.UserRole)
                
                # 移除当前项
                self.subtask_list.takeItem(current_index)
                
                # 在新位置插入
                self.subtask_list.insertItem(current_index + 1, item)
                
                # 重新设置widget（因为takeItem会移除widget）
                old_widget = self.subtask_list.itemWidget(item)  # 这里可能返回None，需要处理
                if old_widget:
                    self.subtask_list.setItemWidget(item, old_widget)
                
                print(f"[INFO] 任务下移: 从索引 {current_index} 到 {current_index + 1}")
                
                # 更新任务的最后修改时间
                if hasattr(self, 'task_data') and isinstance(self.task_data, dict):
                    try:
                        self.task_data['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as time_error:
                        print(f"[WARNING] 更新最后修改时间失败: {str(time_error)}")
        except Exception as e:
            print(f"[ERROR] 移动任务下移时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_subtask_stats(self):
        """更新细碎任务统计信息，增强统计功能、错误处理和用户体验
        
        增强功能：
        - 提供更详细的任务统计数据（总计、已完成、未完成、完成率）
        - 改进错误处理和异常恢复机制
        - 优化性能，减少不必要的嵌套异常
        - 支持进度条可视化和状态信息展示
        """
        try:
            # 确保subtask_list存在
            if not hasattr(self, 'subtask_list'):
                print("[ERROR] subtask_list不存在，无法更新统计信息")
                if hasattr(self, 'stats_label'):
                    self.stats_label.setText("统计信息不可用")
                return
            
            # 基础统计数据初始化
            total = self.subtask_list.count()
            completed = 0
            incomplete = 0
            error_count = 0
            data_quality_issues = 0
            
            # 优化统计逻辑，减少嵌套try-except
            for i in range(total):
                task_completed = False
                item_valid = True
                
                try:
                    item = self.subtask_list.item(i)
                    if not item:
                        print(f"[WARNING] 任务索引 {i} 对应的项不存在")
                        item_valid = False
                        continue
                    
                    # 优先从UserRole获取完成状态（主要数据源）
                    try:
                        data = item.data(Qt.UserRole)
                        if isinstance(data, dict):
                            if 'completed' in data:
                                task_completed = bool(data['completed'])
                            else:
                                # 数据不完整，但仍可统计
                                data_quality_issues += 1
                                print(f"[DEBUG] 任务索引 {i} 数据中缺少'completed'字段")
                        else:
                            print(f"[DEBUG] 任务索引 {i} 的UserRole数据不是字典类型: {type(data)}")
                            # 尝试从widget获取完成状态（备用方案）
                            widget = self.subtask_list.itemWidget(item)
                            if widget:
                                for child in widget.findChildren(QPushButton):
                                    try:
                                        if child.property('is_completed'):
                                            task_completed = True
                                            break
                                    except Exception:
                                        continue
                    except Exception as role_error:
                        print(f"[DEBUG] 任务索引 {i} 从UserRole获取完成状态失败: {str(role_error)}")
                        # 尝试从widget获取完成状态（回退方案）
                        try:
                            widget = self.subtask_list.itemWidget(item)
                            if widget:
                                for child in widget.findChildren(QPushButton):
                                    try:
                                        if child.property('is_completed'):
                                            task_completed = True
                                            break
                                    except Exception:
                                        continue
                        except Exception:
                            pass
                except Exception as item_error:
                    print(f"[ERROR] 统计任务项 {i} 时出错: {str(item_error)}")
                    error_count += 1
                    item_valid = False
                
                if item_valid:
                    if task_completed:
                        completed += 1
                    else:
                        incomplete += 1
            
            # 计算完成率（避免除以零错误）
            completion_rate = 0
            if total > 0:
                completion_rate = round((completed / total) * 100, 1)
            
            # 构建详细的统计信息文本
            status_text = f"完成: {completed} / 未完成: {incomplete} / 总计: {total} ({completion_rate}%)"
            
            # 添加警告信息
            warning_parts = []
            if error_count > 0:
                warning_parts.append(f"错误项: {error_count}")
                print(f"[WARNING] 统计过程中有 {error_count} 个任务项处理出错")
            if data_quality_issues > 0:
                warning_parts.append(f"数据问题: {data_quality_issues}")
                print(f"[WARNING] 统计过程中发现 {data_quality_issues} 个数据质量问题")
            
            if warning_parts:
                status_text += " [" + ", ".join(warning_parts) + "]"
            
            # 更新统计标签
            if hasattr(self, 'stats_label'):
                self.stats_label.setText(status_text)
                
                # 根据完成状态添加颜色样式（如果可能）
                try:
                    if total > 0 and completion_rate == 100:
                        self.stats_label.setStyleSheet("color: green; font-weight: bold;")
                    elif total > 0 and completion_rate > 0:
                        self.stats_label.setStyleSheet("color: orange; font-weight: normal;")
                    else:
                        self.stats_label.setStyleSheet("color: black; font-weight: normal;")
                except Exception:
                    # 样式设置失败不影响功能
                    pass
            else:
                print("[WARNING] stats_label不存在，无法显示统计信息")
            
            # 更新进度条（如果有这个组件）
            if hasattr(self, 'progress_bar'):
                try:
                    if total > 0:
                        self.progress_bar.setValue(int(completion_rate))
                        # 根据完成率设置进度条颜色
                        if completion_rate == 100:
                            self.progress_bar.setStyleSheet("QProgressBar { background-color: #e0ffe0; border: 1px solid #00cc00; } QProgressBar::chunk { background-color: #00cc00; }")
                        elif completion_rate > 50:
                            self.progress_bar.setStyleSheet("QProgressBar { background-color: #fff8e0; border: 1px solid #ffcc00; } QProgressBar::chunk { background-color: #ffcc00; }")
                        else:
                            self.progress_bar.setStyleSheet("QProgressBar { background-color: #ffe0e0; border: 1px solid #ff6666; } QProgressBar::chunk { background-color: #ff6666; }")
                    else:
                        self.progress_bar.setValue(0)
                        self.progress_bar.setStyleSheet("")
                except Exception as pb_error:
                    print(f"[DEBUG] 更新进度条时出错: {str(pb_error)}")
            
            # 记录详细的统计信息日志
            print(f"[DEBUG] 更新任务统计: 总计 {total}, 已完成 {completed}, 未完成 {incomplete}, 完成率 {completion_rate}%")
            if error_count > 0 or data_quality_issues > 0:
                print(f"[DEBUG] 统计警告: 错误项 {error_count}, 数据问题 {data_quality_issues}")
            
        except Exception as e:
            # 最外层异常捕获，确保即使出现严重错误也不会崩溃
            error_msg = f"[ERROR] 更新统计信息时发生严重错误: {str(e)}"
            print(error_msg)
            
            # 出错时显示降级的基本信息
            try:
                basic_info = "统计信息不可用"
                if hasattr(self, 'subtask_list'):
                    try:
                        basic_count = self.subtask_list.count()
                        basic_info = f"统计信息可能不准确 (总计: {basic_count})"
                    except:
                        pass
                
                if hasattr(self, 'stats_label'):
                    self.stats_label.setText(basic_info)
                    self.stats_label.setStyleSheet("color: red; font-weight: bold;")
                
                if hasattr(self, 'progress_bar'):
                    try:
                        self.progress_bar.setValue(0)
                        self.progress_bar.setStyleSheet("QProgressBar { background-color: #ffe0e0; border: 1px solid #ff6666; }")
                    except:
                        pass
                
            except Exception as fallback_error:
                print(f"[CRITICAL] 降级处理统计错误时也失败: {str(fallback_error)}")

        
    def update_task_list(self, task_data=None):
        """更新任务列表显示，增强对细碎任务的处理和错误处理"""
        try:
            # 清空现有列表
            self.subtask_list.clear()
            
            # 如果提供了任务数据，使用它；否则使用当前任务数据
            if task_data is None:
                task_data = self.get_task_data()
            
            # 确保task_data是字典类型
            if not isinstance(task_data, dict):
                print(f"[WARNING] 提供的任务数据不是有效字典: {task_data}")
                task_data = {}
            
            # 确保subtasks字段存在且为列表
            subtasks = task_data.get("subtasks", [])
            if not isinstance(subtasks, list):
                print(f"[WARNING] subtasks字段不是列表类型: {type(subtasks)}")
                subtasks = []
            
            # 添加所有细碎任务到列表
            for index, subtask in enumerate(subtasks):
                try:
                    task_text = ""
                    completed = False
                    
                    if isinstance(subtask, dict):
                        task_text = str(subtask.get("text", "")).strip()
                        completed = bool(subtask.get("completed", False))
                    elif isinstance(subtask, str):
                        # 兼容旧格式
                        task_text = subtask.strip()
                    else:
                        print(f"[WARNING] 无效的细碎任务格式 (索引 {index}): {type(subtask)}")
                        continue
                    
                    if task_text:
                        self.add_subtask_item(task_text, completed)
                        print(f"[DEBUG] 添加细碎任务 {index+1}/{len(subtasks)}: '{task_text}', 完成状态: {completed}")
                except Exception as e:
                    print(f"[ERROR] 处理细碎任务 {index} 时出错: {str(e)}")
            
            # 更新统计信息
            self.update_subtask_stats()
            print(f"[DEBUG] 成功更新任务列表，总计 {self.subtask_list.count()} 个细碎任务")
            
        except Exception as e:
            print(f"[ERROR] 更新任务列表时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 即使出错也要更新统计信息
            self.update_subtask_stats()
    
    def get_task_data(self):
        """获取任务数据，增强数据验证和错误处理，确保与DataManager兼容"""
        try:
            print("[DEBUG] get_task_data方法被调用，开始收集任务数据")
            # 收集任务数据
            subtasks = []
            total_items = self.subtask_list.count()
            print(f"[DEBUG] 细碎任务列表总数量: {total_items}")
            
            for i in range(total_items):
                try:
                    item = self.subtask_list.item(i)
                    if not item:
                        print(f"[WARNING] 任务项 {i} 不存在")
                        continue
                    
                    # 尝试从item的UserRole获取数据（优先）
                    try:
                        data = item.data(Qt.UserRole)
                        if isinstance(data, dict):
                            subtasks.append({
                                'text': str(data.get('text', '')).strip(),
                                'completed': bool(data.get('completed', False))
                            })
                            print(f"[DEBUG] 从UserRole获取任务项 {i+1}/{total_items}: '{data.get('text', '')}', 完成状态: {data.get('completed', False)}")
                            continue
                    except Exception as role_error:
                        print(f"[WARNING] 从UserRole获取数据失败: {str(role_error)}")
                    
                    # 从widget中获取数据（兼容现有实现）
                    widget = self.subtask_list.itemWidget(item)
                    print(f"[DEBUG] 处理任务项 {i+1}/{total_items}, widget: {widget}")
                    
                    if widget:
                        buttons = widget.findChildren(QPushButton)
                        labels = widget.findChildren(QLabel)
                        print(f"[DEBUG] 找到按钮: {len(buttons)}, 找到标签: {len(labels)}")
                        
                        # 查找完成按钮和标签
                        completion_button = None
                        label = None
                        
                        for btn in buttons:
                            if btn.text() in ["完成", "已完成"]:
                                completion_button = btn
                                break
                        
                        if labels:
                            label = labels[0]
                        
                        # 即使找不到按钮或标签，也要尝试收集数据
                        text = ""
                        is_completed = False
                        
                        if label:
                            # 移除HTML标签
                            text = label.text().replace("<s>", "").replace("</s>", "").strip()
                        
                        if completion_button:
                            is_completed = completion_button.property("is_completed") if hasattr(completion_button, 'property') else False
                        
                        # 确保空任务也能被正确处理，避免数据丢失
                        print(f"[DEBUG] 添加任务项 {i+1}/{total_items}: '{text}', 完成状态: {is_completed}")
                        subtasks.append({
                            'text': text,
                            'completed': is_completed
                        })
                    else:
                        print(f"[WARNING] 任务项 {i} 的widget不存在")
                except Exception as item_error:
                    print(f"[ERROR] 处理任务项 {i+1} 时出错: {str(item_error)}")
                    import traceback
                    traceback.print_exc()
                    # 出错时仍然添加一个空任务项，确保数据完整性
                    subtasks.append({'text': '', 'completed': False})
            
            # 获取截止时间，添加异常处理
            deadline_str = ""
            try:
                from PyQt5.QtCore import QDateTime
                if hasattr(self, 'deadline_date') and hasattr(self, 'deadline_time'):
                    deadline_date = self.deadline_date.date()
                    deadline_time = self.deadline_time.time()
                    deadline_dt = QDateTime(deadline_date, deadline_time)
                    deadline_str = deadline_dt.toString("yyyy-MM-dd HH:mm:ss")
                else:
                    print("[WARNING] deadline_date或deadline_time属性不存在")
            except Exception as e:
                print(f"[ERROR] 获取截止时间时出错: {str(e)}")
            
            # 获取任务名称，确保即使出现问题也有默认值
            task_name = ""
            try:
                task_name = self.title_edit.text().strip() if hasattr(self, 'title_edit') else ""
            except Exception as e:
                print(f"[ERROR] 获取任务名称时出错: {str(e)}")
            
            # 获取任务描述，确保即使出现问题也有默认值
            description = ""
            try:
                description = self.description_edit.toPlainText() if hasattr(self, 'description_edit') else ""
            except Exception as e:
                print(f"[ERROR] 获取任务描述时出错: {str(e)}")
            
            # 构建任务数据，确保完整的数据结构
            task_data = {
                'name': task_name if task_name else "未命名任务",
                'description': description,
                'deadline': deadline_str if deadline_str else "无截止日期",
                'subtasks': subtasks,
                'last_modified': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 确保create_time字段存在，与DataManager兼容
            if hasattr(self, 'task_data') and isinstance(self.task_data, dict):
                task_data['create_time'] = self.task_data.get('create_time', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            else:
                task_data['create_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"[DEBUG] get_task_data返回数据: {task_data}")
            return task_data
        except Exception as e:
            print(f"[ERROR] get_task_data方法出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 返回基本数据，确保程序不会崩溃
            try:
                from datetime import datetime
                return {
                    'name': self.title_edit.text().strip() if hasattr(self, 'title_edit') else '未命名任务',
                    'description': self.description_edit.toPlainText() if hasattr(self, 'description_edit') else '',
                    'deadline': '无截止日期',
                    'subtasks': [],  # 确保始终返回列表类型
                    'create_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'last_modified': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            except:
                # 最后的保障，即使datetime导入失败也能返回数据
                return {
                    'name': '未命名任务',
                    'description': '',
                    'deadline': '无截止日期',
                    'subtasks': [],
                    'create_time': '2023-01-01 00:00:00',
                    'last_modified': '2023-01-01 00:00:00'
                }


    def accept(self):
        try:
            # 验证输入
            if not hasattr(self, 'title_edit') or not self.title_edit.text().strip():
                QMessageBox.warning(self, "输入错误", "任务名称不能为空！")
                return
            
            # 显式创建任务数据字典，确保其存在
            if not hasattr(self, 'task_data'):
                self.task_data = {'name': '', 'subtasks': []}
                print("[DEBUG] 创建了新的task_data字典")
            elif not isinstance(self.task_data, dict):
                self.task_data = {'name': '', 'subtasks': []}
                print("[DEBUG] 重置了无效的task_data字典")
            
            # 更新任务数据
            try:
                # 获取并保存任务数据
                new_task_data = self.get_task_data()
                print(f"[DEBUG] 获取到的任务数据: {new_task_data}")
                
                # 确保数据完整性
                if not isinstance(new_task_data, dict):
                    print("[ERROR] get_task_data返回非字典数据，重新初始化")
                    new_task_data = {'name': self.title_edit.text().strip(), 'subtasks': []}
                
                if 'subtasks' not in new_task_data:
                    new_task_data['subtasks'] = []
                    print("[DEBUG] 数据中缺少subtasks字段，已添加")
                elif not isinstance(new_task_data['subtasks'], list):
                    new_task_data['subtasks'] = []
                    print("[DEBUG] subtasks不是列表，已重置")
                
                # 确保任务名称被正确设置
                new_task_data['name'] = self.title_edit.text().strip()
                new_task_data['last_modified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 直接将数据深度复制到self.task_data，确保引用正确
                # 不使用update，直接替换整个字典以避免引用问题
                self.task_data = dict(new_task_data)  # 创建新字典确保独立性
                print(f"[DEBUG] 任务数据已成功深度复制并保存: {self.task_data}")
                
                # 添加额外的数据持久化确认
                if len(self.task_data.get('subtasks', [])) > 0:
                    print(f"[DEBUG] 已保存的细碎任务数量: {len(self.task_data['subtasks'])}")
                    for i, subtask in enumerate(self.task_data['subtasks']):
                        print(f"[DEBUG] 任务 {i+1}: {subtask}")
                else:
                    print("[DEBUG] 当前没有细碎任务")
                    
            except Exception as data_error:
                print(f"[ERROR] 获取任务数据时出错: {str(data_error)}")
                import traceback
                traceback.print_exc()
                # 确保task_data是有效的字典，即使在错误情况下
                self.task_data = {'name': self.title_edit.text().strip(), 'subtasks': []}
                print("[DEBUG] 出错后重置task_data为基本结构")
            
            # 调用父类的accept方法关闭对话框，增加额外的异常处理
            try:
                # 最终验证数据完整性
                if not isinstance(self.task_data, dict):
                    print("[CRITICAL] task_data不是字典，设置默认值")
                    self.task_data = {'name': '未命名任务', 'subtasks': []}
                
                # 确保对话框可以正确关闭并返回数据
                print(f"[DEBUG] 最终任务数据: {self.task_data}")
                
                # 添加直接保存到文件的备用机制
                try:
                    # 尝试从父窗口获取data_manager并直接保存
                    if hasattr(self.parent(), 'task_handler') and hasattr(self.parent().task_handler, 'data_manager'):
                        data_manager = self.parent().task_handler.data_manager
                        print("[DEBUG] 尝试通过父窗口的data_manager直接保存数据")
                        
                        # 获取父窗口中的所有任务
                        all_tasks = self.parent().task_handler.tasks
                        print(f"[DEBUG] 父窗口中的任务数据: {all_tasks}")
                        
                        # 保存所有任务
                        data_manager.save_tasks(all_tasks)
                        print("[DEBUG] 数据已通过data_manager直接保存到文件")
                except Exception as save_error:
                    print(f"[ERROR] 备用保存机制失败: {str(save_error)}")
                    # 即使保存失败，也要继续关闭对话框
                
                print("[DEBUG] 准备调用super().accept()")
                
                # 直接调用accept，不要额外赋值
                super().accept()
                print("[DEBUG] 对话框成功关闭，数据应已返回给父窗口")
                
            except Exception as accept_error:
                print(f"[ERROR] 关闭对话框时出错: {str(accept_error)}")
                import traceback
                traceback.print_exc()
                # 如果调用父类方法失败，尝试手动关闭
                try:
                    print("[DEBUG] 尝试手动关闭对话框")
                    self.done(QDialog.Accepted)
                    print("[DEBUG] 手动关闭对话框成功")
                except Exception as done_error:
                    print(f"[ERROR] 手动关闭对话框也失败: {str(done_error)}")
                    traceback.print_exc()
                    # 最后的尝试 - 强制关闭
                    try:
                        self.hide()
                        print("[DEBUG] 强制隐藏对话框")
                    except:
                        pass
        except Exception as e:
                print(f"[ERROR] accept方法出错: {str(e)}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "错误", f"保存任务时出错: {str(e)}")
    
    def save_task_data(self, force_save=False):
        """保存任务数据，增强数据验证、错误处理和保存机制
        
        参数:
            force_save: 是否强制保存，即使数据看起来为空
            
        返回:
            tuple: (是否保存成功, 错误信息)
        """
        try:
            print("[INFO] 开始保存任务数据")
            
            # 获取并验证任务数据
            task_data = self.get_task_data()
            if not task_data or not isinstance(task_data, dict):
                error_msg = "获取的任务数据无效"
                print(f"[ERROR] {error_msg}")
                return False, error_msg
            
            # 检查是否有实质性数据需要保存，即使只有subtasks也应该保存
            has_content = task_data.get('name') != "未命名任务" or \
                         task_data.get('description', "").strip() or \
                         len(task_data.get('subtasks', [])) > 0
            
            # 即使没有实质内容，如果强制保存或有subtasks也应保存
            if not force_save and not has_content:
                print("[DEBUG] 任务数据为空且非强制保存，跳过保存")
                return True, "无实质内容需要保存"
            
            # 深度复制数据以避免引用问题
            safe_task_data = deepcopy(task_data)
            
            # 数据完整性验证和修复
            required_fields = ['name', 'description', 'deadline', 'subtasks', 'last_modified', 'create_time']
            for field in required_fields:
                if field not in safe_task_data:
                    if field == 'subtasks':
                        safe_task_data[field] = []
                    elif field in ['name', 'description', 'deadline']:
                        safe_task_data[field] = '' if field != 'deadline' else "无截止日期"
                    elif field in ['last_modified', 'create_time']:
                        safe_task_data[field] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[INFO] 补充缺失字段: {field}")
            
            # 确保subtasks是列表类型
            if not isinstance(safe_task_data['subtasks'], list):
                safe_task_data['subtasks'] = []
                print("[WARNING] subtasks字段类型错误，已重置为空列表")
            
            # 验证每个细碎任务的数据结构
            for i, subtask in enumerate(safe_task_data['subtasks']):
                if not isinstance(subtask, dict):
                    # 转换非字典类型的任务
                    if isinstance(subtask, str):
                        safe_task_data['subtasks'][i] = {
                            'text': subtask.strip(),
                            'completed': False
                        }
                        print(f"[INFO] 转换任务项 {i+1} 为字典格式")
                    else:
                        # 删除无效的任务项
                        print(f"[WARNING] 移除无效的任务项 {i+1}: {type(subtask)}")
                        safe_task_data['subtasks'][i] = {'text': '', 'completed': False}
                else:
                    # 确保必要字段存在
                    if 'text' not in subtask:
                        subtask['text'] = ''
                    if 'completed' not in subtask:
                        subtask['completed'] = False
            
            # 清理空任务
            safe_task_data['subtasks'] = [t for t in safe_task_data['subtasks'] if t.get('text', '').strip()]
            
            # 更新self.task_data - 关键修改：使用深度复制确保完全独立
            self.task_data = deepcopy(safe_task_data)  # 使用深度复制避免任何引用问题
            print(f"[DEBUG] 任务数据已成功更新: {self.task_data.get('name')}")
            print(f"[DEBUG] 细碎任务数量: {len(self.task_data.get('subtasks', []))}")
            for i, subtask in enumerate(self.task_data.get('subtasks', [])):
                print(f"  - 细碎任务{i+1}: {subtask.get('text', '')} (完成: {subtask.get('completed', False)})")
            
            # 尝试多种保存机制
            save_attempts = []
            save_success = False
            
            # 保存机制1: 如果有task_handler和task_index，通过task_handler更新
            if hasattr(self, 'task_handler') and hasattr(self, 'task_index'):
                try:
                    task_type = getattr(self, 'task_type', 'tasks')
                    success = self.task_handler.update_task(task_type, self.task_index, safe_task_data)
                    save_attempts.append(f"task_handler.update_task: {'success' if success else 'failed'}")
                    if success:
                        save_success = True
                        print("[INFO] 通过task_handler成功保存任务数据")
                except Exception as handler_error:
                    error_msg = f"task_handler保存失败: {str(handler_error)}"
                    save_attempts.append(error_msg)
                    print(f"[ERROR] {error_msg}")
            
            # 保存机制2: 尝试通过父窗口的data_manager保存
            if not save_success and hasattr(self.parent(), 'task_handler') and hasattr(self.parent().task_handler, 'data_manager'):
                try:
                    data_manager = self.parent().task_handler.data_manager
                    all_tasks = self.parent().task_handler.tasks
                    data_manager.save_tasks(all_tasks)
                    save_attempts.append("parent.data_manager.save_tasks: success")
                    save_success = True
                    print("[INFO] 通过父窗口的data_manager成功保存任务数据")
                except Exception as parent_error:
                    error_msg = f"父窗口data_manager保存失败: {str(parent_error)}"
                    save_attempts.append(error_msg)
                    print(f"[ERROR] {error_msg}")
            
            # 保存机制3: 如果有直接的data_manager引用，使用它
            if not save_success and hasattr(self, 'data_manager'):
                try:
                    self.data_manager.save_tasks(self.tasks if hasattr(self, 'tasks') else {})
                    save_attempts.append("self.data_manager.save_tasks: success")
                    save_success = True
                    print("[INFO] 通过自身的data_manager成功保存任务数据")
                except Exception as self_dm_error:
                    error_msg = f"自身data_manager保存失败: {str(self_dm_error)}"
                    save_attempts.append(error_msg)
                    print(f"[ERROR] {error_msg}")
            
            # 新增保存机制4: 如果以上都失败，直接将task_data保存到父对象（如果有）
            if not save_success and hasattr(self, 'parent') and hasattr(self.parent(), 'update_task_item'):
                try:
                    # 获取任务索引（如果有）
                    task_index = getattr(self, 'task_index', -1)
                    if task_index >= 0:
                        self.parent().update_task_item(task_index, safe_task_data)
                        save_attempts.append("parent.update_task_item: success")
                        save_success = True
                        print("[INFO] 通过父对象的update_task_item成功保存任务数据")
                except Exception as parent_update_error:
                    error_msg = f"父对象update_task_item保存失败: {str(parent_update_error)}"
                    save_attempts.append(error_msg)
                    print(f"[ERROR] {error_msg}")
            
            # 记录保存结果
            print(f"[INFO] 任务数据保存尝试完成，结果: {'成功' if save_success else '失败'}")
            for attempt in save_attempts:
                print(f"  - {attempt}")
            
            # 返回保存结果和信息
            if save_success:
                return True, "任务数据保存成功"
            else:
                # 即使无法持久化，任务数据也已更新到self.task_data
                print("[WARNING] 所有保存机制失败，但任务数据已更新到内存中")
                return False, f"所有保存机制失败，但任务数据已更新到内存中: {'; '.join(save_attempts)}"
                
        except Exception as e:
            error_msg = f"保存任务数据时发生严重错误: {str(e)}"
            print(f"[ERROR] {error_msg}")
            # 确保task_data仍然有效
            try:
                if not hasattr(self, 'task_data') or not isinstance(self.task_data, dict):
                    self.task_data = {'name': '未命名任务', 'subtasks': []}
                print("[DEBUG] 出错后确保task_data有效")
            except:
                pass
            
            return False, error_msg
    
    def closeEvent(self, event):
        """对话框关闭事件处理，增强数据保存逻辑和用户提示"""
        try:
            # 关键修改：强制保存数据，特别是细碎任务数据，即使没有明显的内容变化
            # 这样可以确保用户添加的细碎任务在关闭对话框时不会丢失
            success, message = self.save_task_data(force_save=True)
            
            # 如果保存失败，显示警告但不阻止关闭
            if not success and "无实质内容" not in message:
                QMessageBox.warning(self, "保存提示", f"任务数据保存情况: {message}")
            
            # 确保数据已经正确更新
            print("[INFO] 对话框关闭，任务数据已保存")
            if hasattr(self, 'task_data') and isinstance(self.task_data, dict):
                subtask_count = len(self.task_data.get('subtasks', []))
                print(f"[DEBUG] 关闭时确认细碎任务数量: {subtask_count}")
            
            # 调用父类方法确保正常关闭
            super().closeEvent(event)
            
        except Exception as e:
            print(f"[ERROR] 处理关闭事件时出错: {str(e)}")
            # 即使出错也要关闭对话框
            event.accept()
