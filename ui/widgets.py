from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget,
                             QPushButton, QGroupBox, QHBoxLayout,
                             QListWidgetItem, QLabel)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette


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
        # 序号保持默认黑色（不设置颜色）
        main_layout.addWidget(index_label)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)

        lines = text.split('\n')
        if len(lines) >= 3:
            # 事务名称（纯黑色）
            name_label = QLabel(lines[0])
            name_font = QFont()
            name_font.setPointSize(13)
            name_font.setBold(True)
            name_label.setFont(name_font)
            # 不设置文本颜色，使用默认黑色
            content_layout.addWidget(name_label)

            # 重要度和紧急度（纯黑色）
            info_label = QLabel(lines[1])
            info_font = QFont()
            info_font.setPointSize(11)
            info_label.setFont(info_font)
            # 不设置文本颜色，使用默认黑色
            content_layout.addWidget(info_label)

            # 时间信息（纯黑色，仅调整字体大小）
            time_label = QLabel(lines[2])
            time_font = QFont()
            time_font.setPointSize(9)
            time_label.setFont(time_font)
            # 关键：移除时间标签的颜色设置，使用默认黑色
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
        item.setSizeHint(QSize(0, 95))
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, task_widget)

    def clear_list(self):
        self.list_widget.clear()

    def get_selected_index(self):
        selected = self.list_widget.selectedItems()
        return self.list_widget.row(selected[0]) if selected else -1