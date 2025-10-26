from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget,
                             QPushButton, QGroupBox, QHBoxLayout,
                             QListWidgetItem, QLabel)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette
from datetime import datetime


class TaskItemWidget(QWidget):
    def __init__(self, text, index, parent=None, urgency=1, is_overdue=False, is_done=False):
        super().__init__(parent)
        self.index = index
        self.urgency = urgency
        self.is_overdue = is_overdue
        self.is_done = is_done
        self.setAutoFillBackground(True)
        self.init_ui(text)

    def init_ui(self, text):
        # 统一浅蓝色背景
        self.setStyleSheet("""
            padding: 0px;
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)

        # 左侧紧急度/状态色块
        color_bar = QWidget()
        color_bar.setFixedWidth(6)
        color_bar.setStyleSheet(f"border-radius: 3px; {self.get_color_style()}")
        main_layout.addWidget(color_bar)

        # 序号标签
        index_label = QLabel(f"{self.index}.")
        index_font = QFont()
        index_font.setPointSize(11)
        index_font.setBold(True)
        index_label.setFont(index_font)
        index_label.setAlignment(Qt.AlignTop | Qt.AlignRight)
        index_label.setFixedWidth(25)
        main_layout.addWidget(index_label)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)

        lines = text.split('\n')
        
        # 确保至少有1行文本
        if len(lines) >= 1:
            # 事务名称（纯黑色）
            name_label = QLabel(lines[0])
            name_font = QFont()
            name_font.setPointSize(13)
            name_font.setBold(True)
            name_label.setFont(name_font)
            content_layout.addWidget(name_label)

        # 重要度和紧急度信息
        if len(lines) >= 2:
            info_label = QLabel(lines[1])
            info_font = QFont()
            info_font.setPointSize(11)
            info_label.setFont(info_font)
            content_layout.addWidget(info_label)

        # 创建时间和截止日期信息
        if len(lines) >= 3:
            datetime_label = QLabel(lines[2])
            datetime_font = QFont()
            datetime_font.setPointSize(10)
            datetime_label.setFont(datetime_font)
            content_layout.addWidget(datetime_label)
        
        # 类别和标签信息（如果有）
        for i in range(3, len(lines) - 1):  # 跳过最后一行（倒计时信息）
            meta_label = QLabel(lines[i])
            meta_font = QFont()
            meta_font.setPointSize(10)
            # 为类别和标签添加样式
            if lines[i].startswith("类别:"):
                meta_label.setStyleSheet("color: rgb(100, 100, 200);")  # 类别显示蓝色
            elif lines[i].startswith("标签:"):
                meta_label.setStyleSheet("color: rgb(100, 180, 100);")  # 标签显示绿色
            meta_label.setFont(meta_font)
            content_layout.addWidget(meta_label)

        # 倒计时信息（总是最后一行，突出显示，加粗）
        if len(lines) >= 1:
            time_label = QLabel(lines[-1])
            time_font = QFont()
            time_font.setPointSize(10)
            time_font.setBold(True)  # 倒计时信息加粗显示
            time_label.setFont(time_font)
            
            # 根据倒计时内容设置不同颜色
            if "已超时" in lines[-1]:
                time_label.setStyleSheet("color: rgb(220, 50, 50);")  # 超时显示红色
            elif "剩余" in lines[-1]:
                # 检查剩余时间，如果小于1天则显示橙色
                if any(part in lines[-1] for part in ["分钟", "小时"]) and "天" not in lines[-1]:
                    time_label.setStyleSheet("color: rgb(245, 120, 0);")  # 短时间显示橙色
                else:
                    time_label.setStyleSheet("color: rgb(0, 80, 150);")  # 正常剩余时间显示蓝色
            
            content_layout.addWidget(time_label)
        else:
            label = QLabel(text)
            content_layout.addWidget(label)

        main_layout.addLayout(content_layout)
        main_layout.addStretch(1)

        # 已完成任务添加删除线（不改变颜色）
        if self.is_done:
            for i in range(content_layout.count()):
                widget = content_layout.itemAt(i).widget()
                if isinstance(widget, QLabel):
                    font = widget.font()
                    font.setStrikeOut(True)
                    widget.setFont(font)

    def get_color_style(self):
        """左侧色块颜色逻辑"""
        if self.is_overdue:
            return "background-color: rgb(255, 90, 90);"  # 超时-红色
        elif self.is_done:
            return "background-color: rgb(150, 150, 150);"  # 已完成-灰色
        else:
            urgency_colors = {
                1: "background-color: rgb(255, 90, 90);",  # 最紧急-红色
                2: "background-color: rgb(255, 170, 70);",  # 紧急-橙色
                3: "background-color: rgb(255, 210, 0);",  # 中等-黄色
                4: "background-color: rgb(100, 200, 120);",  # 较不紧急-绿色
                5: "background-color: rgb(80, 150, 255);"  # 最不紧急-深蓝色
            }
            return urgency_colors.get(self.urgency, "background-color: rgb(200, 200, 200);")
    
    def update_time_display(self):
        """更新任务的时间显示"""
        # 获取内容布局中的最后一个标签（应该是时间标签）
        main_layout = self.layout()
        content_layout = main_layout.itemAt(2).layout()  # 获取内容布局
        
        if content_layout.count() >= 4:  # 确保至少有4个标签
            time_label = content_layout.itemAt(3).widget()  # 第4个标签是时间标签
            datetime_label = content_layout.itemAt(2).widget()  # 第3个标签包含日期信息
            
            # 解析datetime_label中的内容，提取截止日期
            datetime_text = datetime_label.text()
            if "截止日期：" in datetime_text:
                # 提取截止日期部分
                deadline_str = datetime_text.split("截止日期：")[1].strip()
                
                # 计算并更新倒计时
                if deadline_str != "无截止日期":
                    # 解析截止日期时间
                    try:
                        # 假设格式为 "2024-10-25 23:59:59"
                        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
                        now = datetime.now()
                        
                        if now > deadline:
                            # 超时
                            self.is_overdue = True
                            time_label.setText("已超时")
                            time_label.setStyleSheet("color: rgb(220, 50, 50);")  # 超时显示红色
                            
                            # 更新左侧色块为红色
                            color_bar = main_layout.itemAt(0).widget()
                            color_bar.setStyleSheet("border-radius: 3px; background-color: rgb(255, 90, 90);")
                        else:
                            # 计算剩余时间
                            remaining = deadline - now
                            days = remaining.days
                            hours, remainder = divmod(remaining.seconds, 3600)
                            minutes, seconds = divmod(remainder, 60)
                            
                            # 格式化剩余时间显示
                            if days > 0:
                                time_text = f"剩余：{days}天{hours}小时"
                                time_label.setStyleSheet("color: rgb(0, 80, 150);")  # 正常剩余时间显示蓝色
                            elif hours > 0:
                                time_text = f"剩余：{hours}小时{minutes}分钟"
                                time_label.setStyleSheet("color: rgb(245, 120, 0);")  # 短时间显示橙色
                            else:
                                time_text = f"剩余：{minutes}分钟{seconds}秒"
                                time_label.setStyleSheet("color: rgb(245, 120, 0);")  # 短时间显示橙色
                            
                            time_label.setText(time_text)
                    except ValueError:
                        # 如果解析失败，保持原样
                        pass
                else:
                    # 无截止日期，保持原样
                    pass


class TaskListWidget(QWidget):
    def __init__(self, task_type, parent=None):
        super().__init__(parent)
        self.task_type = task_type
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(False)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setSpacing(8)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                background-color: #ffffff;
            }
            QListWidget::item {
                margin: 3px 0;
            }
            QListWidget::item:selected {
                background-color: #e6f2ff;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.list_widget)

        # 按钮样式（增大尺寸）
        btn_style = """
            QPushButton {
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #ccc;
                background-color: #f5f5f5;
                margin: 4px 0;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e9e9e9;
            }
        """

        if self.task_type in ["todo", "overdue"]:
            self.done_btn = QPushButton("标记为完成")
            self.done_btn.setMinimumHeight(36)  # 增大按钮高度
            self.done_btn.setStyleSheet(btn_style + "font-weight: bold;")
            layout.addWidget(self.done_btn)

        self.delete_btn = QPushButton("删除任务")
        self.delete_btn.setMinimumHeight(36)  # 增大按钮高度
        self.delete_btn.setStyleSheet(btn_style)
        layout.addWidget(self.delete_btn)

    def add_task_item(self, task_text, index, urgency=1, is_overdue=False, is_done=False):
        task_widget = TaskItemWidget(
            task_text,
            index,
            urgency=urgency,
            is_overdue=is_overdue,
            is_done=is_done
        )
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 150))  # 增加高度以容纳更多信息，避免文本遮挡
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, task_widget)

    def clear_list(self):
        self.list_widget.clear()

    def get_selected_index(self):
        selected = self.list_widget.selectedItems()
        return self.list_widget.row(selected[0]) if selected else -1

    def update_time_display(self):
        """更新列表中所有任务的时间显示"""
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            task_widget = self.list_widget.itemWidget(item)
            if hasattr(task_widget, 'update_time_display'):
                task_widget.update_time_display()