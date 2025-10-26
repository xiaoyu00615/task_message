from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget,
                             QPushButton, QGroupBox, QHBoxLayout,
                             QListWidgetItem, QLabel, QProgressBar)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette
from datetime import datetime


def format_time_display(days, hours, minutes, seconds, is_overdue=False):
    """
    统一的时间格式化函数，确保初始化和更新使用相同的格式
    使用与task_handler.py中相同的格式：半角冒号+单位间空格
    当剩余时间为0分钟时开始显示秒数
    """
    parts = []
    
    # 添加调试信息
    print(f"format_time_display输入 - 天: {days}, 小时: {hours}, 分钟: {minutes}, 秒: {seconds}, 超时: {is_overdue}")
    
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    
    # 总是显示分钟（除非没有其他时间单位且秒数为0）
    if minutes > 0 or (not parts and seconds == 0):
        parts.append(f"{minutes}分钟")
    
    # 关键逻辑修改：当分钟为0且小时和天都为0时，无论秒数是否为0都显示秒数
    # 这样就能确保在任务剩余时间为0分钟时显示秒数
    if not days and not hours and minutes == 0:
        parts.append(f"{seconds}秒")
    # 原来的条件保留，确保在小时和天都为0时，如果秒数大于0也显示秒数
    elif seconds > 0 and not hours and not days:
        parts.append(f"{seconds}秒")
    
    print(f"format_time_display输出 - 时间部分: {parts}")
    
    # 使用半角冒号而不是全角冒号，单位之间添加空格
    prefix = "已超时: " if is_overdue else "剩余: "
    return f"{prefix}{' '.join(parts)}"


class TaskItemWidget(QWidget):
    def __init__(self, text, index, parent=None, urgency=1, is_overdue=False, is_done=False, create_time=None, deadline=None, done_time=None):
        super().__init__(parent)
        self.index = index
        self.urgency = urgency
        self.is_overdue = is_overdue
        self.is_done = is_done
        self.create_time = create_time
        self.deadline = deadline
        self.done_time = done_time
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
            # 首先添加创建时间
            create_time_text = ""
            if self.create_time:
                create_time_text = f"创建时间：{self.create_time}"
            else:
                # 尝试从原始文本中提取创建时间
                if "创建时间" in lines[2]:
                    create_time_parts = lines[2].split("创建时间：")
                    if len(create_time_parts) > 1:
                        create_time_text = f"创建时间：{create_time_parts[1].split('截止')[0].strip()}"
            
            if create_time_text:
                create_label = QLabel(create_time_text)
                create_font = QFont()
                create_font.setPointSize(10)
                create_label.setFont(create_font)
                create_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                content_layout.addWidget(create_label)
            
            # 对于已完成任务，在创建时间和截止日期之间添加完成日期
            # 即使done_time为None，也显示完成日期标签，使用当前时间作为默认值
            if self.is_done:
                # 如果没有提供done_time，使用当前时间作为默认值
                display_time = self.done_time if self.done_time else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                done_label = QLabel(f"完成日期：{display_time}")
                done_font = QFont()
                done_font.setPointSize(10)
                done_font.setBold(True)  # 完成日期加粗显示
                done_label.setFont(done_font)
                
                # 检查是否为超时完成
                is_overdue_completion = False
                if self.deadline and self.deadline != "无截止日期" and display_time:
                    try:
                        # 解析完成时间和截止时间
                        done_dt = datetime.strptime(display_time, "%Y-%m-%d %H:%M:%S")
                        # 尝试多种格式解析截止日期
                        deadline_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
                        deadline_dt = None
                        for fmt in deadline_formats:
                            try:
                                deadline_dt = datetime.strptime(self.deadline, fmt)
                                break
                            except ValueError:
                                continue
                        # 如果都成功解析且完成时间晚于截止日期，则为超时完成
                        if deadline_dt and done_dt > deadline_dt:
                            is_overdue_completion = True
                    except:
                        # 解析失败时默认为正常完成
                        pass
                
                # 根据是否超时完成设置不同颜色
                if is_overdue_completion:
                    done_label.setStyleSheet("color: rgb(220, 50, 50);")  # 超时完成显示红色
                else:
                    done_label.setStyleSheet("color: rgb(100, 180, 100);")  # 正常完成显示绿色
                
                done_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                content_layout.addWidget(done_label)
            
            # 添加截止日期
            deadline_text = ""
            if self.deadline and self.deadline != "无截止日期":
                deadline_text = f"截止日期：{self.deadline}"
            else:
                # 尝试从原始文本中提取截止日期
                if "截止日期" in lines[2]:
                    deadline_parts = lines[2].split("截止日期：")
                    if len(deadline_parts) > 1:
                        deadline_text = f"截止日期：{deadline_parts[1].strip()}"
                elif "截止：" in lines[2]:
                    deadline_parts = lines[2].split("截止：")
                    if len(deadline_parts) > 1:
                        deadline_text = f"截止日期：{deadline_parts[1].strip()}"
            
            if deadline_text:
                deadline_label = QLabel(deadline_text)
                deadline_font = QFont()
                deadline_font.setPointSize(10)
                deadline_label.setFont(deadline_font)
                deadline_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                content_layout.addWidget(deadline_label)
        
        # 类别和标签信息（如果有）
        for i in range(3, len(lines) - 1):  # 跳过最后一行（倒计时信息）
            # 跳过包含截止日期的行，避免重复显示
            if any(keyword in lines[i] for keyword in ["截止日期", "截止"]):
                continue
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

        # 倒计时信息（总是最后一行，突出显示，加粗）- 仅非已完成任务显示
        if len(lines) >= 1 and not self.is_done:
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
            
            # 添加进度条 - 仅非已完成任务显示
            self.progress_bar = QProgressBar()
            # 设置统一的进度条大小和样式
            self.set_progress_bar_style()
            
            # 初始进度设置
            progress_value = self.calculate_progress()
            self.progress_bar.setValue(progress_value)
            
            # 不在这里直接设置进度条颜色，而是让set_progress_bar_style方法根据紧急度自动设置
            # 只确保显示百分比文本
            self.progress_bar.setTextVisible(True)
            
            content_layout.addWidget(self.progress_bar)
        # 已完成任务显示状态提示
        elif self.is_done:
            # 检查是否为超时完成
            is_overdue_completion = False
            # 尝试多种方式获取完成时间
            # 1. 首先从文本中提取完成日期
            display_done_time = None
            for line in lines:
                if "完成日期：" in line:
                    parts = line.split("完成日期：")
                    if len(parts) > 1:
                        display_done_time = parts[1].strip()
                        break
            # 2. 如果文本中没有，使用self.done_time
            if not display_done_time:
                display_done_time = self.done_time
            
            # 3. 如果都没有，使用当前时间作为默认值（确保有值）
            if not display_done_time:
                display_done_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 简单的调试输出
            print(f"调试 - 任务: {lines[0]}, 完成时间: {display_done_time}, 截止日期: {self.deadline}")
            
            # 判断是否超时完成
            if display_done_time and self.deadline and self.deadline != "无截止日期":
                # 先尝试直接字符串比较（最可靠）
                try:
                    # 提取日期部分进行比较
                    done_date_str = display_done_time[:10]  # 提取 YYYY-MM-DD 部分
                    deadline_date_str = self.deadline[:10]  # 提取 YYYY-MM-DD 部分
                    
                    print(f"调试 - 比较日期: {done_date_str} vs {deadline_date_str}")
                    
                    # 直接字符串比较（YYYY-MM-DD格式可以直接比较）
                    if done_date_str > deadline_date_str:
                        is_overdue_completion = True
                        print("调试 - 判断为超时完成")
                    else:
                        print("调试 - 判断为正常完成")
                except:
                    # 字符串比较失败时，尝试使用datetime解析
                    try:
                        # 解析完成时间
                        if ' ' in display_done_time:
                            done_dt = datetime.strptime(display_done_time, "%Y-%m-%d %H:%M:%S")
                        else:
                            done_dt = datetime.strptime(display_done_time, "%Y-%m-%d")
                        
                        # 解析截止日期
                        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
                            try:
                                deadline_dt = datetime.strptime(self.deadline, fmt)
                                if done_dt > deadline_dt:
                                    is_overdue_completion = True
                                break
                            except:
                                continue
                    except:
                        pass
            
            # 强制设置标签文本和颜色
            label_text = "[超时完成]" if is_overdue_completion else "[已完成]"
            label_color = "color: rgb(220, 50, 50);" if is_overdue_completion else "color: rgb(100, 180, 100);"
            
            print(f"调试 - 最终标签: {label_text}, 颜色: {label_color}")
            
            done_label = QLabel(label_text)
            done_label.setStyleSheet(label_color)  # 直接设置样式
                
            done_font = QFont()
            done_font.setPointSize(10)
            done_font.setBold(True)
            done_label.setFont(done_font)
            content_layout.addWidget(done_label)
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

    def set_progress_bar_style(self, color=None):
        """统一设置进度条样式和大小，背景使用对应紧急度的淡色，进度填充使用紧急度颜色，不使用黑色文本"""
        # 设置固定的高度和大小属性
        self.progress_bar.setMinimumHeight(12)
        self.progress_bar.setMaximumHeight(12)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(True)
        
        # 获取对应紧急度的背景颜色（淡色）
        urgency_bg_color = self.get_urgency_bg_color()
        
        # 如果没有传入颜色参数，获取对应紧急度的填充颜色（原色）
        if color is None:
            color = self.get_urgency_chunk_color()
        
        # 使用字符串拼接而不是f-string，避免CSS大括号导致的语法错误
        style_sheet = ""
        style_sheet += "QProgressBar {\n"
        style_sheet += "    border: 1px solid #ccc;\n"
        style_sheet += "    border-radius: 6px;\n"
        style_sheet += "    background-color: " + urgency_bg_color + ";\n"
        style_sheet += "    text-align: center;\n"
        style_sheet += "    font-size: 10px;\n"
        style_sheet += "    font-weight: bold;\n"
        style_sheet += "    min-height: 12px;\n"
        style_sheet += "    max-height: 12px;\n"
        style_sheet += "    color: #333;  /* 使用深灰色而非黑色 */\n"
        style_sheet += "}\n"
        style_sheet += "QProgressBar::chunk {\n"
        style_sheet += "    background-color: " + color + ";\n"
        style_sheet += "    border-radius: 5px;\n"
        style_sheet += "}\n"
        
        self.progress_bar.setStyleSheet(style_sheet)
        
    def get_urgency_bg_color(self):
        """根据紧急度获取进度条背景颜色"""
        # 使用与左侧色块类似但稍浅的颜色作为背景
        urgency_colors = {
            1: "#ffe0e0",  # 最紧急-浅红色
            2: "#fff0e0",  # 紧急-浅橙色
            3: "#ffffe0",  # 中等-浅黄色
            4: "#e0ffe0",  # 较不紧急-浅绿色
            5: "#e0f0ff"   # 最不紧急-浅蓝色
        }
        if self.is_overdue:
            return "#ffe0e0"  # 超时使用浅红色背景
        elif self.is_done:
            return "#f0f0f0"  # 已完成使用灰色背景
        return urgency_colors.get(self.urgency, "#f0f0f0")
        
    def get_urgency_chunk_color(self):
        """根据紧急度获取进度条填充颜色（chunk颜色）"""
        # 使用与左侧色块相同的颜色作为进度条填充色
        urgency_colors = {
            1: "rgb(255, 90, 90)",  # 最紧急-红色
            2: "rgb(255, 170, 70)",  # 紧急-橙色
            3: "rgb(255, 210, 0)",  # 中等-黄色
            4: "rgb(100, 200, 120)",  # 较不紧急-绿色
            5: "rgb(80, 150, 255)"  # 最不紧急-深蓝色
        }
        if self.is_overdue:
            return "rgb(255, 90, 90)"  # 超时使用红色
        elif self.is_done:
            return "rgb(150, 150, 150)"  # 已完成使用灰色
        return urgency_colors.get(self.urgency, "rgb(100, 180, 250)")

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
    
    def calculate_progress(self):
        """根据创建时间和截止日期计算任务进度"""
        if not self.create_time or not self.deadline or self.deadline == "无截止日期":
            return 0
        
        try:
            # 解析创建时间和截止日期
            create_datetime = datetime.strptime(self.create_time, "%Y-%m-%d %H:%M:%S")
            
            # 尝试解析包含时间的格式
            try:
                deadline_datetime = datetime.strptime(self.deadline, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    deadline_datetime = datetime.strptime(self.deadline, "%Y-%m-%d %H:%M")
                except ValueError:
                    # 回退到旧格式（仅日期）
                    deadline_datetime = datetime.strptime(self.deadline, "%Y-%m-%d")
            
            now = datetime.now()
            
            # 计算总时间跨度（从创建到截止）
            total_duration = deadline_datetime - create_datetime
            if total_duration.total_seconds() <= 0:
                return 100  # 无效的时间范围，认为已超时
            
            # 计算已过时间
            elapsed = now - create_datetime
            
            # 计算进度百分比
            progress_percentage = (elapsed.total_seconds() / total_duration.total_seconds()) * 100
            
            # 确保进度在0-100之间
            return min(max(int(progress_percentage), 0), 100)
        except Exception as e:
            return 0  # 解析错误时返回0
    
    def calculate_progress(self):
        """计算任务进度百分比"""
        if self.deadline and self.create_time and self.deadline != '无截止日期':
            # 计算时间百分比
            now = datetime.now()
            try:
                # 解析创建时间
                create_dt = datetime.strptime(self.create_time, '%Y-%m-%d %H:%M:%S')
                
                # 尝试不同的截止日期格式
                try:
                    # 尝试带时间的格式
                    deadline_dt = datetime.strptime(self.deadline, '%Y-%m-%d %H:%M')
                except ValueError:
                    # 尝试只有日期的格式
                    deadline_dt = datetime.strptime(self.deadline, '%Y-%m-%d')
                    # 设置时间为当天的午夜
                    deadline_dt = deadline_dt.replace(hour=23, minute=59, second=59)
                
                # 计算总时间和已用时间
                total_time = (deadline_dt - create_dt).total_seconds()
                elapsed_time = (now - create_dt).total_seconds()
                
                # 确保不会出现负数百分比
                if elapsed_time < 0:
                    elapsed_time = 0
                
                # 计算时间百分比
                time_percentage = (elapsed_time / total_time) * 100 if total_time > 0 else 0
                
                # 确保百分比在0-100之间
                if time_percentage > 100:
                    time_percentage = 100
                
                return int(time_percentage)
            except ValueError:
                # 日期格式解析错误，返回0
                return 0
        return 0
    
    def _find_datetime_label(self, content_layout):
        """查找包含日期信息的标签，优先找到包含截止日期的标签"""
        # 首先尝试找到明确的截止日期标签
        deadline_label = None
        create_time_label = None
        
        for i in range(content_layout.count()):
            widget = content_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                text = widget.text()
                # 优先识别截止日期标签
                if any(keyword in text for keyword in ["截止日期", "截止", "完成日期", "期限", "deadline"]):
                    deadline_label = widget
                    print(f"找到明确的截止日期标签: {text}")
                    return deadline_label
                # 记录创建时间标签（作为后备）
                elif "创建时间" in text or "创建" in text:
                    create_time_label = widget
                    print(f"找到创建时间标签: {text}")
                # 检查是否包含多个日期（可能同时包含创建和截止日期）
                elif any(char.isdigit() for char in text) and any(sep in text for sep in ["-", "/", "年", "月", "日"]) and text.count(":") >= 2:
                    print(f"找到可能包含多个日期的标签: {text}")
                    return widget
        
        # 如果没有明确的截止日期标签，但有创建时间标签，也返回它
        if create_time_label:
            print("没有找到截止日期标签，使用创建时间标签作为后备")
            return create_time_label
        
        # 如果没找到特定标签，返回第三个QLabel（这是原始逻辑中的位置）
        for i in range(content_layout.count()):
            widget = content_layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and i >= 2:  # 尝试第三个及以后的标签
                print(f"回退到默认标签位置 {i}: {widget.text()}")
                return widget
        
        print("未找到任何可能的日期标签")
        return None
    
    def _find_time_label(self, content_layout):
        """查找显示倒计时的标签"""
        # 在初始化时，时间标签是最后一个添加的QLabel（在进度条之前）
        # 从后往前查找，寻找加粗且包含剩余或超时文本的标签
        for i in range(content_layout.count() - 1, -1, -1):
            widget = content_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                font = widget.font()
                text = widget.text()
                if font.bold() and ("剩余" in text or "已超时" in text):
                    return widget
        # 如果没找到符合条件的标签，返回最后一个QLabel
        for i in range(content_layout.count() - 1, -1, -1):
            widget = content_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                return widget
        return None
        
    def update_time_display(self):
        """更新任务的时间显示"""
        # 添加日志输出
        print(f"更新任务时间显示 - 任务索引: {self.index}")
        
        # 获取内容布局
        main_layout = self.layout()
        if not main_layout or main_layout.count() <= 2:
            print(f"任务{self.index}: 未找到有效布局")
            return
            
        content_layout_item = main_layout.itemAt(2)
        if not content_layout_item or not hasattr(content_layout_item, 'layout'):
            print(f"任务{self.index}: 未找到内容布局")
            return
            
        content_layout = content_layout_item.layout()
        
        # 使用更智能的方式查找标签
        datetime_label = self._find_datetime_label(content_layout)
        time_label = self._find_time_label(content_layout)
        
        if not datetime_label:
            print(f"任务{self.index}: 未找到日期时间标签")
        if not time_label:
            print(f"任务{self.index}: 未找到时间标签")
        if not datetime_label or not time_label:
            return
            
        print(f"任务{self.index}: 找到标签，开始更新倒计时")
            
        # 解析日期信息，尝试提取截止日期
        datetime_text = datetime_label.text()
        print(f"正在解析日期文本: {datetime_text}")
        
        # 尝试多种方式提取截止日期
        deadline_str = None
        
        # 1. 检查是否包含明确的截止日期标识
        if "截止日期：" in datetime_text:
            deadline_str = datetime_text.split("截止日期：")[1].strip()
            # 如果提取的字符串较长，可能包含额外信息，尝试找到第一个有效的日期部分
            if len(deadline_str) > 20:
                import re
                # 尝试匹配日期时间格式
                date_match = re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(:\d{2})?', deadline_str)
                if date_match:
                    deadline_str = date_match.group(0)
        elif "截止：" in datetime_text:
            deadline_str = datetime_text.split("截止：")[1].strip()
        elif "完成日期：" in datetime_text:
            deadline_str = datetime_text.split("完成日期：")[1].strip()
        elif "期限：" in datetime_text:
            deadline_str = datetime_text.split("期限：")[1].strip()
        
        # 2. 如果文本包含多个日期，尝试提取第二个日期（通常是截止日期）
        if not deadline_str and datetime_text.count(" ") >= 3:
            import re
            # 尝试找到所有日期时间格式
            dates = re.findall(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(:\d{2})?', datetime_text)
            if len(dates) >= 2:
                deadline_str = dates[1]  # 使用第二个日期作为截止日期
                print(f"提取到第二个日期作为截止日期: {deadline_str}")
        
        # 使用对象的deadline属性
        if not deadline_str and hasattr(self, 'deadline') and self.deadline and self.deadline != "无截止日期":
            deadline_str = self.deadline
            print(f"使用对象的deadline属性: {deadline_str}")
        
        # 如果找到截止日期信息
        if deadline_str and deadline_str != "无截止日期":
            print(f"最终确定的截止日期: {deadline_str}")
            # 尝试多种日期格式解析
            deadline = None
            formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
            
            for fmt in formats:
                try:
                    deadline = datetime.strptime(deadline_str, fmt)
                    break
                except ValueError:
                    continue
            
            if deadline:
                now = datetime.now()
                
                if now > deadline:
                    # 超时，计算超时时间
                    self.is_overdue = True
                    overdue = now - deadline
                    days = overdue.days
                    hours, remainder = divmod(overdue.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    # 使用统一的格式化函数
                    time_text = format_time_display(days, hours, minutes, seconds, is_overdue=True)
                    
                    # 确保字体设置与初始化时一致（加粗且大小为10）
                    time_font = QFont()
                    time_font.setPointSize(10)
                    time_font.setBold(True)
                    time_label.setFont(time_font)
                    time_label.setStyleSheet("color: rgb(220, 50, 50);")  # 超时显示红色
                    
                    # 更新左侧色块为红色
                    color_bar_item = main_layout.itemAt(0)
                    if color_bar_item:
                        color_bar = color_bar_item.widget()
                        if color_bar:
                            color_bar.setStyleSheet("border-radius: 3px; background-color: rgb(255, 90, 90);")
                    
                    # 直接更新标签文本，确保立即生效
                    old_text = time_label.text()
                    time_label.setText(time_text)
                    time_label.update()  # 强制更新显示
                    print(f"任务{self.index}: 超时显示已更新 - 从 '{old_text}' 到 '{time_text}'")
                    
                    # 更新进度条
                    if hasattr(self, 'progress_bar'):
                        progress_value = self.calculate_progress()
                        self.progress_bar.setValue(progress_value)
                        self.progress_bar.update()  # 强制更新进度条
                        self.set_progress_bar_style()
                        print(f"任务{self.index}: 进度条已更新为 {progress_value}%")
                else:
                    # 计算剩余时间
                    remaining = deadline - now
                    days = remaining.days
                    hours, remainder = divmod(remaining.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    # 添加调试信息
                    print(f"任务{self.index}: 剩余时间计算 - 天: {days}, 小时: {hours}, 分钟: {minutes}, 秒: {seconds}")
                    
                    # 使用统一的格式化函数
                    time_text = format_time_display(days, hours, minutes, seconds, is_overdue=False)
                    print(f"任务{self.index}: 格式化后的时间文本: '{time_text}'")
                    # 确保字体设置与初始化时一致（加粗且大小为10）
                    time_font = QFont()
                    time_font.setPointSize(10)
                    time_font.setBold(True)
                    time_label.setFont(time_font)
                    
                    # 根据剩余时间设置颜色
                    if days > 0:
                        time_label.setStyleSheet("color: rgb(0, 80, 150);")  # 正常剩余时间显示蓝色
                    else:
                        time_label.setStyleSheet("color: rgb(245, 120, 0);")  # 短时间显示橙色
                    
                    # 直接更新标签文本，确保立即生效
                    old_text = time_label.text()
                    time_label.setText(time_text)
                    time_label.update()  # 强制更新显示
                    print(f"任务{self.index}: 倒计时已更新 - 从 '{old_text}' 到 '{time_text}'")
                    
                    # 更新进度条
                    if hasattr(self, 'progress_bar'):
                        progress_value = self.calculate_progress()
                        self.progress_bar.setValue(progress_value)
                        self.progress_bar.update()  # 强制更新进度条
                        self.set_progress_bar_style()
                        print(f"任务{self.index}: 进度条已更新为 {progress_value}%")
                    
    def update_task_text(self, text):
        """更新任务文本内容"""
        main_layout = self.layout()
        content_layout = main_layout.itemAt(2).layout()  # 获取内容布局
        
        # 更新第一行文本（任务名称）
        if content_layout.count() > 0:
            first_label = content_layout.itemAt(0).widget()
            if isinstance(first_label, QLabel):
                lines = text.split('\n')
                if lines:
                    first_label.setText(lines[0])
        
    def set_urgency(self, urgency, is_overdue=False):
        """设置任务紧急度并更新相关样式"""
        self.urgency = urgency
        self.is_overdue = is_overdue
        
        # 更新左侧色块颜色
        main_layout = self.layout()
        color_bar = main_layout.itemAt(0).widget()
        color_bar.setStyleSheet(f"border-radius: 3px; {self.get_color_style()}")
        
        # 更新进度条样式
        if hasattr(self, 'progress_bar'):
            self.set_progress_bar_style()
            # 重新计算进度
            progress_value = self.calculate_progress()
            self.progress_bar.setValue(progress_value)


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

    def add_task_item(self, task_text, index, urgency=1, is_overdue=False, is_done=False, create_time=None, deadline=None, done_time=None):
        task_widget = TaskItemWidget(
            task_text,
            index,
            urgency=urgency,
            is_overdue=is_overdue,
            is_done=is_done,
            create_time=create_time,
            deadline=deadline,
            done_time=done_time
        )
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 200))  # 进一步增加高度，确保所有任务项（包括第三项）都能完全显示所有内容
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, task_widget)

    def clear_list(self):
        self.list_widget.clear()

    def get_selected_index(self):
        selected = self.list_widget.selectedItems()
        return self.list_widget.row(selected[0]) if selected else -1

    def save_scroll_position(self):
        """保存当前列表的滚动位置"""
        return self.list_widget.verticalScrollBar().value()

    def restore_scroll_position(self, position):
        """恢复列表的滚动位置"""
        self.list_widget.verticalScrollBar().setValue(position)

    def update_time_display(self):
        """更新列表中所有任务的时间显示，同时保留滚动位置"""
        # 保存当前滚动位置
        scroll_pos = self.save_scroll_position()
        
        # 更新所有任务的时间显示
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            task_widget = self.list_widget.itemWidget(item)
            if hasattr(task_widget, 'update_time_display'):
                task_widget.update_time_display()
        
        # 恢复滚动位置
        self.restore_scroll_position(scroll_pos)