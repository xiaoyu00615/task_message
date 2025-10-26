#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计界面组件
负责显示各种任务统计图表
"""

import csv
import os
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                            QGroupBox, QPushButton, QDateEdit, QSpinBox, QFormLayout,
                            QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

# 软导入matplotlib，防止应用崩溃
try:
    # 简化导入方式，先导入基本模块
    import matplotlib
    print(f"Matplotlib版本: {matplotlib.__version__}")
    # 设置后端
    matplotlib.use('Agg')  # 先使用非交互式后端
    import matplotlib.pyplot as plt
    # 然后再导入Qt相关组件
    try:
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        import matplotlib.dates as mdates
        MATPLOTLIB_AVAILABLE = True
        print("Matplotlib和Qt5后端成功导入")
    except ImportError:
        print("警告: Qt5后端不可用，尝试使用基本功能")
        # 即使Qt5后端不可用，也使用基本的Figure
        from matplotlib.figure import Figure
        FigureCanvas = None  # 标记为None
        import matplotlib.dates as mdates
        MATPLOTLIB_AVAILABLE = True
        print("Matplotlib基本功能可用")
except ImportError as e:
    print(f"错误: matplotlib导入失败 - {str(e)}")
    MATPLOTLIB_AVAILABLE = False
    # 创建模拟类以防止崩溃
    class MockCanvas(QWidget):
        def __init__(self, parent=None, width=5, height=4, dpi=100):
            super().__init__(parent)
            self.fig = None
            self.axes = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Matplotlib not available"))
        
        def draw(self):
            pass
    
    class MockFigure:
        def __init__(self, **kwargs):
            self.axes = []
        
        def add_subplot(self, *args):
            class MockAxes:
                def clear(self): pass
                def plot(self, *args, **kwargs): pass
                def set_title(self, *args): pass
                def set_xlabel(self, *args): pass
                def set_ylabel(self, *args): pass
                def tick_params(self, *args, **kwargs): pass
                def grid(self, *args, **kwargs): pass
                def pie(self, *args, **kwargs): pass
                def axis(self, *args): pass
                def bar(self, *args, **kwargs): pass
            
            mock_axes = MockAxes()
            self.axes.append(mock_axes)
            return mock_axes
        
        def tight_layout(self):
            pass
        
        def savefig(self, *args, **kwargs):
            pass
    
    class MockDates:
        pass
    
    FigureCanvas = MockCanvas
    Figure = MockFigure
    mdates = MockDates()
    plt = None
except Exception as e:
    print(f"错误: matplotlib初始化失败 - {str(e)}")
    MATPLOTLIB_AVAILABLE = False
    # 创建模拟类以防止崩溃
    class MockCanvas(QWidget):
        def __init__(self, parent=None, width=5, height=4, dpi=100):
            super().__init__(parent)
            self.fig = None
            self.axes = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Matplotlib not available"))
        
        def draw(self):
            pass
    
    class MockFigure:
        def __init__(self, **kwargs):
            self.axes = []
        
        def add_subplot(self, *args):
            class MockAxes:
                def clear(self): pass
                def plot(self, *args, **kwargs): pass
                def set_title(self, *args): pass
                def set_xlabel(self, *args): pass
                def set_ylabel(self, *args): pass
                def tick_params(self, *args, **kwargs): pass
                def grid(self, *args, **kwargs): pass
                def pie(self, *args, **kwargs): pass
                def axis(self, *args): pass
                def bar(self, *args, **kwargs): pass
            
            mock_axes = MockAxes()
            self.axes.append(mock_axes)
            return mock_axes
        
        def tight_layout(self):
            pass
        
        def savefig(self, *args, **kwargs):
            pass
    
    class MockDates:
        pass
    
    FigureCanvas = MockCanvas
    Figure = MockFigure
    mdates = MockDates()
    plt = None

from core.statistics_manager import StatisticsManager


class MatplotlibCanvas(QWidget):
    """
    Matplotlib图表画布组件
    自适应处理matplotlib可用性和Qt5后端可用性
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super(MatplotlibCanvas, self).__init__(parent)
        
        if MATPLOTLIB_AVAILABLE:
            try:
                self.fig = Figure(figsize=(width, height), dpi=dpi)
                self.axes = self.fig.add_subplot(111)
                
                # 设置中文字体
                plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
                plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
                
                # 如果FigureCanvas可用，创建画布
                if FigureCanvas is not None:
                    self.canvas = FigureCanvas(self.fig)
                    layout = QVBoxLayout(self)
                    layout.addWidget(self.canvas)
                    layout.setContentsMargins(0, 0, 0, 0)
                else:
                    # Qt5后端不可用时，显示提示
                    layout = QVBoxLayout(self)
                    layout.addWidget(QLabel("Matplotlib图表功能受限(缺少Qt5后端)"))
                    print("警告: 缺少Qt5后端，图表显示功能受限")
                
                self.fig.tight_layout()
            except Exception as e:
                print(f"错误: 创建图表画布失败 - {str(e)}")
                self.axes = None
                self.fig = None
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel("图表初始化失败"))
        else:
            # matplotlib不可用时
            self.axes = None
            self.fig = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Matplotlib not available"))
    
    def draw(self):
        """
        绘制图表
        """
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'canvas') and self.canvas is not None:
            try:
                self.canvas.draw()
            except Exception as e:
                print(f"错误: 绘制图表失败 - {str(e)}")
    
    def clear(self):
        """清空画布"""
        if MATPLOTLIB_AVAILABLE and hasattr(self, 'axes') and self.axes is not None:
            try:
                self.axes.clear()
            except Exception as e:
                print(f"错误: 清空图表失败 - {str(e)}")


class TrendChartWidget(QWidget):
    """
    任务趋势图表组件
    """
    def __init__(self, statistics_manager, parent=None):
        super(TrendChartWidget, self).__init__(parent)
        self.statistics_manager = statistics_manager
        self.init_ui()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建控制栏
        control_layout = QHBoxLayout()
        
        # 统计周期选择
        period_label = QLabel("统计周期:")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["每日", "每周", "每月"])
        self.period_combo.currentTextChanged.connect(self.update_chart)
        
        # 统计天数选择
        days_label = QLabel("统计天数:")
        self.days_spin = QSpinBox()
        self.days_spin.setRange(7, 365)
        self.days_spin.setValue(30)
        self.days_spin.setSingleStep(7)
        self.days_spin.valueChanged.connect(self.update_chart)
        
        # 导出按钮
        export_chart_btn = QPushButton("导出图表")
        export_chart_btn.clicked.connect(self.export_chart)
        
        export_data_btn = QPushButton("导出数据")
        export_data_btn.clicked.connect(self.export_data)
        
        control_layout.addWidget(period_label)
        control_layout.addWidget(self.period_combo)
        control_layout.addWidget(days_label)
        control_layout.addWidget(self.days_spin)
        control_layout.addWidget(export_chart_btn)
        control_layout.addWidget(export_data_btn)
        control_layout.addStretch()
        
        # 创建图表
        self.canvas = MatplotlibCanvas(self, width=8, height=5)
        
        # 添加到主布局
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.canvas)
        
        # 初始更新图表
        self.update_chart()
    
    def export_chart(self):
        """
        导出当前图表为图片文件
        """
        # 打开文件对话框
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出图表", "", "PNG Files (*.png);;JPEG Files (*.jpg);;SVG Files (*.svg);;PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                # 保存图表
                self.canvas.fig.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", "图表导出成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"图表导出失败：{str(e)}")
    
    def export_data(self):
        """
        导出趋势数据为CSV文件
        """
        # 获取当前统计数据
        period_text = self.period_combo.currentText()
        period_map = {"每日": "daily", "每周": "weekly", "每月": "monthly"}
        period = period_map.get(period_text, "daily")
        days = self.days_spin.value()
        
        labels, values = self.statistics_manager.get_completion_trend(period, days)
        
        # 打开文件对话框
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "", "CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if filename:
            try:
                # 写入CSV文件
                with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    # 写入表头
                    writer.writerow(["时间", "完成任务数量"])
                    # 写入数据
                    for label, value in zip(labels, values):
                        writer.writerow([label, value])
                
                QMessageBox.information(self, "成功", "数据导出成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"数据导出失败：{str(e)}")
    
    def update_chart(self):
        # 清空图表
        self.canvas.clear()
        
        # 检查matplotlib可用性
        if not MATPLOTLIB_AVAILABLE:
            return
            
        # 获取统计周期和天数
        period_text = self.period_combo.currentText()
        period_map = {"每日": "daily", "每周": "weekly", "每月": "monthly"}
        period = period_map.get(period_text, "daily")
        days = self.days_spin.value()
        
        # 获取趋势数据
        labels, values = self.statistics_manager.get_completion_trend(period, days)
        
        # 绘制折线图
        self.canvas.axes.plot(labels, values, marker='o', linestyle='-', linewidth=2, markersize=5)
        
        # 设置图表标题和标签
        title_map = {"daily": "每日", "weekly": "每周", "monthly": "每月"}
        self.canvas.axes.set_title(f"{title_map.get(period, '每日')}完成任务数量趋势")
        self.canvas.axes.set_xlabel("时间")
        self.canvas.axes.set_ylabel("完成任务数量")
        
        # 设置x轴标签角度
        if len(labels) > 7:
            self.canvas.axes.tick_params(axis='x', rotation=45)
        
        # 添加网格
        self.canvas.axes.grid(True, linestyle='--', alpha=0.7)
        
        # 重新绘制图表
        self.canvas.fig.tight_layout()
        self.canvas.draw()


class DistributionChartWidget(QWidget):
    """
    任务分布图表组件
    """
    def __init__(self, statistics_manager, parent=None):
        super(DistributionChartWidget, self).__init__(parent)
        self.statistics_manager = statistics_manager
        self.init_ui()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建控制栏
        control_layout = QHBoxLayout()
        
        # 分布类型选择
        type_label = QLabel("分布类型:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["类别分布", "标签分布"])
        self.type_combo.currentTextChanged.connect(self.update_chart)
        
        # 图表类型选择
        chart_label = QLabel("图表类型:")
        self.chart_combo = QComboBox()
        self.chart_combo.addItems(["饼图", "条形图"])
        self.chart_combo.currentTextChanged.connect(self.update_chart)
        
        # 导出按钮
        export_chart_btn = QPushButton("导出图表")
        export_chart_btn.clicked.connect(self.export_chart)
        
        export_data_btn = QPushButton("导出数据")
        export_data_btn.clicked.connect(self.export_data)
        
        control_layout.addWidget(type_label)
        control_layout.addWidget(self.type_combo)
        control_layout.addWidget(chart_label)
        control_layout.addWidget(self.chart_combo)
        control_layout.addWidget(export_chart_btn)
        control_layout.addWidget(export_data_btn)
        control_layout.addStretch()
        
        # 创建图表
        self.canvas = MatplotlibCanvas(self, width=8, height=5)
        
        # 添加到主布局
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.canvas)
        
        # 初始更新图表
        self.update_chart()
    
    def export_chart(self):
        """
        导出当前图表为图片文件
        """
        # 打开文件对话框
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出图表", "", "PNG Files (*.png);;JPEG Files (*.jpg);;SVG Files (*.svg);;PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                # 保存图表
                self.canvas.fig.savefig(filename, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", "图表导出成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"图表导出失败：{str(e)}")
    
    def export_data(self):
        """
        导出分布数据为CSV文件
        """
        # 获取当前统计数据
        dist_type = self.type_combo.currentText()
        
        if dist_type == "类别分布":
            labels, values = self.statistics_manager.get_category_distribution()
            header = ["类别", "任务数量"]
        else:
            labels, values = self.statistics_manager.get_label_distribution()
            header = ["标签", "任务数量"]
        
        # 打开文件对话框
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "", "CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        if filename:
            try:
                # 写入CSV文件
                with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    # 写入表头
                    writer.writerow(header)
                    # 写入数据
                    for label, value in zip(labels, values):
                        writer.writerow([label, value])
                
                QMessageBox.information(self, "成功", "数据导出成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"数据导出失败：{str(e)}")
    
    def update_chart(self):
        # 清空图表
        self.canvas.clear()
        
        # 检查matplotlib可用性
        if not MATPLOTLIB_AVAILABLE:
            return
            
        # 获取分布类型和图表类型
        dist_type = self.type_combo.currentText()
        chart_type = self.chart_combo.currentText()
        
        # 获取分布数据
        if dist_type == "类别分布":
            labels, values = self.statistics_manager.get_category_distribution()
            title = "任务类别分布"
        else:
            labels, values = self.statistics_manager.get_label_distribution()
            title = "任务标签分布"
        
        # 限制显示数量，避免图表过于拥挤
        max_display = 10
        if len(labels) > max_display:
            labels = labels[:max_display]
            values = values[:max_display]
        
        # 绘制图表
        if chart_type == "饼图":
            # 绘制饼图
            self.canvas.axes.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            self.canvas.axes.axis('equal')  # 保持饼图为正圆形
        else:
            # 绘制条形图
            self.canvas.axes.bar(labels, values)
            self.canvas.axes.set_xlabel("类别" if dist_type == "类别分布" else "标签")
            self.canvas.axes.set_ylabel("任务数量")
            self.canvas.axes.tick_params(axis='x', rotation=45)
        
        # 设置图表标题
        self.canvas.axes.set_title(title)
        
        # 重新绘制图表
        self.canvas.fig.tight_layout()
        self.canvas.draw()


class StatisticsCardWidget(QWidget):
    """
    统计数据卡片组件
    显示任务完成率和平均完成时间等统计数据
    """
    def __init__(self, statistics_manager, parent=None):
        super(StatisticsCardWidget, self).__init__(parent)
        self.statistics_manager = statistics_manager
        self.file_path = None
        self.init_ui()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建控制栏
        control_layout = QHBoxLayout()
        
        # 统计天数选择
        days_label = QLabel("统计天数:")
        self.days_spin = QSpinBox()
        self.days_spin.setRange(7, 365)
        self.days_spin.setValue(30)
        self.days_spin.setSingleStep(7)
        self.days_spin.valueChanged.connect(self.update_stats)
        
        # 更新按钮
        update_btn = QPushButton("更新数据")
        update_btn.clicked.connect(self.update_stats)
        
        # 导出统计数据按钮
        export_stats_btn = QPushButton("导出统计数据")
        export_stats_btn.clicked.connect(self.export_stats)
        
        control_layout.addWidget(days_label)
        control_layout.addWidget(self.days_spin)
        control_layout.addWidget(update_btn)
        control_layout.addWidget(export_stats_btn)
        control_layout.addStretch()
        
        # 创建统计卡片布局
        cards_layout = QHBoxLayout()
        
        # 完成率卡片
        self.completion_rate_group = QGroupBox("任务按时完成率")
        self.completion_rate_layout = QFormLayout()
        self.total_tasks_label = QLabel("0")
        self.on_time_tasks_label = QLabel("0")
        self.rate_label = QLabel("0.00%")
        
        # 设置标签字体
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.rate_label.setFont(font)
        
        self.completion_rate_layout.addRow("总任务数:", self.total_tasks_label)
        self.completion_rate_layout.addRow("按时完成:", self.on_time_tasks_label)
        self.completion_rate_layout.addRow("完成率:", self.rate_label)
        self.completion_rate_group.setLayout(self.completion_rate_layout)
        
        # 平均完成时间卡片
        self.avg_time_group = QGroupBox("平均完成任务时间")
        self.avg_time_layout = QFormLayout()
        self.count_label = QLabel("0")
        self.avg_hours_label = QLabel("0")
        self.avg_minutes_label = QLabel("0")
        self.total_avg_label = QLabel("0小时0分钟")
        
        # 设置标签字体
        self.total_avg_label.setFont(font)
        
        self.avg_time_layout.addRow("统计任务数:", self.count_label)
        self.avg_time_layout.addRow("平均小时:", self.avg_hours_label)
        self.avg_time_layout.addRow("平均分钟:", self.avg_minutes_label)
        self.avg_time_layout.addRow("平均总时间:", self.total_avg_label)
        self.avg_time_group.setLayout(self.avg_time_layout)
        
        # 添加卡片到布局
        cards_layout.addWidget(self.completion_rate_group)
        cards_layout.addWidget(self.avg_time_group)
        
        # 添加到主布局
        main_layout.addLayout(control_layout)
        main_layout.addLayout(cards_layout)
        
        # 初始更新统计数据
        self.update_stats()
    
    def export_stats(self):
        """
        导出统计卡片数据为CSV文件
        """
        # 获取统计天数
        days = self.days_spin.value()
        
        # 获取真正的总任务数（所有任务）
        actual_total_count = self.statistics_manager.get_total_tasks_count()
        
        # 获取完成率数据
        _, on_time_count, completion_rate = self.statistics_manager.get_completion_rate(days)
        
        # 获取平均完成时间数据
        count, avg_hours, avg_minutes = self.statistics_manager.get_average_completion_time(days)
        
        # 打开文件对话框
        filename, _ = QFileDialog.getSaveFileName(
            self, "导出统计数据", "", "CSV Files (*.csv);;Text Files (*.txt)"
        )
        
        # 更新file_path属性
        self.file_path = filename
        
        if filename:
            try:
                # 写入CSV文件
                with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    # 写入表头
                    writer.writerow(["统计项目", "数值"])
                    # 写入完成率数据
                    writer.writerow(["统计天数", days])
                    writer.writerow([])  # 空行
                    writer.writerow(["任务按时完成率统计", ""])
                    writer.writerow(["总任务数", actual_total_count])
                    writer.writerow(["按时完成任务数", on_time_count])
                    writer.writerow(["按时完成率", f"{completion_rate:.2f}%"])
                    # 写入平均完成时间数据
                    writer.writerow([])  # 空行
                    writer.writerow(["平均完成任务时间统计", ""])
                    writer.writerow(["统计任务数", count])
                    writer.writerow(["平均小时数", avg_hours])
                    writer.writerow(["平均分钟数", avg_minutes])
                    writer.writerow(["平均总时间", f"{avg_hours}小时{avg_minutes}分钟"])
                
                QMessageBox.information(self, "成功", "统计数据导出成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"统计数据导出失败：{str(e)}")
    
    def update_stats(self):
        # 确保在matplotlib不可用时也能正常工作
        if not MATPLOTLIB_AVAILABLE:
            # 即使matplotlib不可用，统计数据也应继续显示
            pass
        else:
            # 清空画布以防在某些情况下需要更新
            if hasattr(self, 'canvas') and self.canvas is not None:
                self.canvas.clear()
            
        # 获取统计天数
        days = self.days_spin.value()
        
        # 获取真正的总任务数（所有任务）
        actual_total_count = self.statistics_manager.get_total_tasks_count()
        
        # 更新完成率数据
        _, on_time_count, completion_rate = self.statistics_manager.get_completion_rate(days)
        self.total_tasks_label.setText(str(actual_total_count))
        self.on_time_tasks_label.setText(str(on_time_count))
        self.rate_label.setText(f"{completion_rate:.2f}%")
        
        # 更新平均完成时间数据
        count, avg_hours, avg_minutes = self.statistics_manager.get_average_completion_time(days)
        self.count_label.setText(str(count))
        self.avg_hours_label.setText(str(avg_hours))
        self.avg_minutes_label.setText(str(avg_minutes))
        self.total_avg_label.setText(f"{avg_hours}小时{avg_minutes}分钟")


class StatisticsWidget(QWidget):
    """
    统计界面主组件
    整合所有统计图表和功能
    """
    def __init__(self, task_handler, parent=None):
        super(StatisticsWidget, self).__init__(parent)
        self.task_handler = task_handler
        self.statistics_manager = StatisticsManager(task_handler)
        self.init_ui()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标题和整体导出按钮
        title_layout = QHBoxLayout()
        
        # 创建标题
        title_label = QLabel("任务统计与报表")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        title_label.setFont(font)
        
        # 整体导出按钮
        export_all_btn = QPushButton("导出所有数据")
        export_all_btn.clicked.connect(self.export_all_data)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(export_all_btn)
        title_layout.setAlignment(title_label, Qt.AlignCenter)
        
        # 创建统计卡片组件
        stats_card_widget = StatisticsCardWidget(self.statistics_manager)
        
        # 创建图表容器布局
        charts_layout = QHBoxLayout()
        
        # 创建趋势图组件
        trend_widget = TrendChartWidget(self.statistics_manager)
        
        # 创建分布图组件
        distribution_widget = DistributionChartWidget(self.statistics_manager)
        
        # 添加图表到布局
        charts_layout.addWidget(trend_widget)
        charts_layout.addWidget(distribution_widget)
        
        # 添加到主布局
        main_layout.addLayout(title_layout)
        main_layout.addWidget(stats_card_widget)
        main_layout.addLayout(charts_layout)
        
        # 设置布局
        self.setLayout(main_layout)
    
    def export_all_data(self):
        """
        导出所有统计数据为CSV文件
        确保在matplotlib不可用时也能正常工作
        """
        # 打开文件夹对话框选择保存位置
        folder = QFileDialog.getExistingDirectory(self, "选择保存位置")
        
        if folder:
            try:
                # 即使matplotlib不可用，数据导出功能也应继续工作
                if not MATPLOTLIB_AVAILABLE:
                    QMessageBox.information(self, "提示", "Matplotlib不可用，但数据导出功能仍可正常使用。")
                
                # 导出任务趋势数据（每日、每周、每月）
                periods = [("每日", "daily"), ("每周", "weekly"), ("每月", "monthly")]
                
                for period_name, period in periods:
                    labels, values = self.statistics_manager.get_completion_trend(period, 30)
                    filename = os.path.join(folder, f"任务趋势_{period_name}.csv")
                    
                    with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                        writer = csv.writer(file)
                        writer.writerow(["时间", "完成任务数量"])
                        for label, value in zip(labels, values):
                            writer.writerow([label, value])
                
                # 导出类别分布数据
                categories, values = self.statistics_manager.get_category_distribution()
                filename = os.path.join(folder, "任务类别分布.csv")
                with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    writer.writerow(["类别", "任务数量"])
                    for category, value in zip(categories, values):
                        writer.writerow([category, value])
                
                # 导出标签分布数据
                labels, values = self.statistics_manager.get_label_distribution()
                filename = os.path.join(folder, "任务标签分布.csv")
                with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    writer.writerow(["标签", "任务数量"])
                    for label, value in zip(labels, values):
                        writer.writerow([label, value])
                
                # 导出完成率和平均完成时间数据
                filename = os.path.join(folder, "任务完成率和平均时间统计.csv")
                
                # 获取完成率数据（30天）
                total_count, on_time_count, completion_rate = self.statistics_manager.get_completion_rate(30)
                
                # 获取平均完成时间数据（30天）
                count, avg_hours, avg_minutes = self.statistics_manager.get_average_completion_time(30)
                
                with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    # 写入表头
                    writer.writerow(["统计项目", "数值"])
                    # 写入完成率数据
                    writer.writerow(["统计天数", "30"])
                    writer.writerow([])  # 空行
                    writer.writerow(["任务按时完成率统计", ""])
                    writer.writerow(["总任务数", total_count])
                    writer.writerow(["按时完成任务数", on_time_count])
                    writer.writerow(["按时完成率", f"{completion_rate:.2f}%"])
                    # 写入平均完成时间数据
                    writer.writerow([])  # 空行
                    writer.writerow(["平均完成任务时间统计", ""])
                    writer.writerow(["统计任务数", count])
                    writer.writerow(["平均小时数", avg_hours])
                    writer.writerow(["平均分钟数", avg_minutes])
                    writer.writerow(["平均总时间", f"{avg_hours}小时{avg_minutes}分钟"])
                
                QMessageBox.information(self, "成功", f"所有统计数据已导出到文件夹：\n{folder}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"数据导出失败：{str(e)}")
