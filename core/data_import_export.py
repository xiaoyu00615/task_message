import json
import csv
import os
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QHeaderView
from PyQt5.QtCore import Qt
import copy

class DataImportExport:
    """任务数据的导入导出管理类"""
    
    def __init__(self, task_handler):
        self.task_handler = task_handler
    
    def export_tasks(self, export_format, file_path):
        """导出任务数据到指定格式的文件"""
        try:
            if export_format == "json":
                return self._export_json(file_path)
            elif export_format == "csv":
                return self._export_csv(file_path)
            else:
                QMessageBox.warning(None, "错误", f"不支持的导出格式: {export_format}")
                return False
        except Exception as e:
            QMessageBox.warning(None, "导出失败", f"导出数据时出错: {str(e)}")
            return False
    
    def _export_json(self, file_path):
        """导出任务数据为JSON格式"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.task_handler.tasks, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            raise e
    
    def _export_csv(self, file_path):
        """导出任务数据为CSV格式"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow(['任务类型', '任务名称', '重要度', '紧急度', '创建时间', '截止日期', '完成时间', '类别', '标签'])
                
                # 写入数据
                for task_type in ['todo', 'overdue', 'done']:
                    for task in self.task_handler.tasks[task_type]:
                        # 处理标签字段，将列表转换为逗号分隔的字符串
                        tags = ', '.join(task.get('tags', [])) if 'tags' in task and task['tags'] else ''
                        
                        row = [
                            task_type,
                            task.get('name', ''),
                            task.get('importance', 1),
                            task.get('urgency', 3),
                            task.get('create_time', ''),
                            task.get('deadline', '无截止日期'),
                            task.get('done_time', '') if task_type == 'done' else '',
                            task.get('category', '') if 'category' in task else '',
                            tags
                        ]
                        writer.writerow(row)
            return True
        except Exception as e:
            raise e
    
    def import_tasks(self, import_format, file_path, conflict_strategy='skip'):
        """从指定格式的文件导入任务数据"""
        try:
            imported_tasks = []
            
            if import_format == "json":
                imported_tasks = self._import_json(file_path)
            elif import_format == "csv":
                imported_tasks = self._import_csv(file_path)
            else:
                QMessageBox.warning(None, "错误", f"不支持的导入格式: {import_format}")
                return False, []
            
            # 处理导入的任务和可能的冲突
            return self._process_imported_tasks(imported_tasks, conflict_strategy)
        except Exception as e:
            QMessageBox.warning(None, "导入失败", f"导入数据时出错: {str(e)}")
            return False, []
    
    def _import_json(self, file_path):
        """从JSON文件导入任务数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取所有任务
            imported_tasks = []
            for task_type in ['todo', 'overdue', 'done']:
                if task_type in data:
                    for task in data[task_type]:
                        task_copy = copy.deepcopy(task)
                        task_copy['_imported_type'] = task_type
                        imported_tasks.append(task_copy)
            
            return imported_tasks
        except Exception as e:
            raise e
    
    def _import_csv(self, file_path):
        """从CSV文件导入任务数据"""
        try:
            imported_tasks = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    task = {
                        'name': row.get('任务名称', '未命名任务'),
                        'importance': int(row.get('重要度', 1)),
                        'urgency': int(row.get('紧急度', 3)),
                        'deadline': row.get('截止日期', '无截止日期'),
                        '_imported_type': row.get('任务类型', 'todo')
                    }
                    
                    # 可选字段
                    if row.get('创建时间'):
                        task['create_time'] = row['创建时间']
                    if row.get('完成时间'):
                        task['done_time'] = row['完成时间']
                    if row.get('类别'):
                        task['category'] = row['类别']
                    if row.get('标签'):
                        task['tags'] = [tag.strip() for tag in row['标签'].split(',')]
                    
                    imported_tasks.append(task)
            
            return imported_tasks
        except Exception as e:
            raise e
    
    def _process_imported_tasks(self, imported_tasks, conflict_strategy):
        """处理导入的任务，处理可能的冲突"""
        added_count = 0
        skipped_count = 0
        updated_count = 0
        conflict_list = []
        
        # 创建任务标识映射以检测冲突
        existing_tasks_map = {}
        for task_type in ['todo', 'overdue', 'done']:
            for task in self.task_handler.tasks[task_type]:
                task_id = self._get_task_identifier(task)
                existing_tasks_map[task_id] = (task_type, task)
        
        for imported_task in imported_tasks:
            task_id = self._get_task_identifier(imported_task)
            
            # 检查是否存在冲突
            if task_id in existing_tasks_map:
                conflict_list.append(imported_task)
                if conflict_strategy == 'skip':
                    skipped_count += 1
                    continue
                elif conflict_strategy == 'replace':
                    # 替换现有任务
                    existing_type, existing_task = existing_tasks_map[task_id]
                    for i, task in enumerate(self.task_handler.tasks[existing_type]):
                        if self._get_task_identifier(task) == task_id:
                            self.task_handler.tasks[existing_type][i] = imported_task
                            updated_count += 1
                            break
                elif conflict_strategy == 'create_new':
                    # 创建新任务，生成新的创建时间
                    imported_task['create_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    task_type = imported_task['_imported_type']
                    self.task_handler.tasks[task_type].append(imported_task)
                    added_count += 1
            else:
                # 无冲突，直接添加
                task_type = imported_task['_imported_type']
                # 如果没有创建时间，添加当前时间
                if 'create_time' not in imported_task:
                    imported_task['create_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.task_handler.tasks[task_type].append(imported_task)
                added_count += 1
        
        # 保存更新后的任务数据
        if added_count > 0 or updated_count > 0:
            self.task_handler.data_manager.save_tasks(self.task_handler.tasks)
        
        # 返回结果
        return True, {
            'added': added_count,
            'skipped': skipped_count,
            'updated': updated_count,
            'conflicts': conflict_list
        }
    
    def _get_task_identifier(self, task):
        """获取任务的唯一标识符"""
        # 优先使用创建时间和名称作为唯一标识
        if 'create_time' in task and task['create_time']:
            return f"{task['create_time']}_{task.get('name', '').strip()}"
        # 如果没有创建时间，仅使用名称
        return f"unnamed_{task.get('name', '').strip()}"
    
    def show_import_preview_dialog(self, parent, imported_tasks):
        """显示导入数据的预览对话框"""
        dialog = ImportPreviewDialog(parent, imported_tasks)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_selected_strategy(), dialog.get_selected_tasks()
        return None, []


class ImportPreviewDialog(QDialog):
    """导入预览对话框，用于显示待导入的数据并选择冲突处理策略"""
    
    def __init__(self, parent, imported_tasks):
        super().__init__(parent)
        self.imported_tasks = imported_tasks
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("导入预览")
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout(self)
        
        # 标题标签
        title_label = QLabel(f"即将导入 {len(self.imported_tasks)} 个任务")
        layout.addWidget(title_label)
        
        # 任务预览表格
        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(len(self.imported_tasks))
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(['选择', '任务类型', '任务名称', '重要度', '紧急度', '截止日期'])
        
        # 填充表格
        for row, task in enumerate(self.imported_tasks):
            # 选择复选框
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Checked)
            self.table_widget.setItem(row, 0, checkbox_item)
            
            # 任务类型
            task_type_item = QTableWidgetItem(task.get('_imported_type', 'todo'))
            self.table_widget.setItem(row, 1, task_type_item)
            
            # 任务名称
            name_item = QTableWidgetItem(task.get('name', '未命名任务'))
            self.table_widget.setItem(row, 2, name_item)
            
            # 重要度
            importance_item = QTableWidgetItem(str(task.get('importance', 1)))
            self.table_widget.setItem(row, 3, importance_item)
            
            # 紧急度
            urgency_item = QTableWidgetItem(str(task.get('urgency', 3)))
            self.table_widget.setItem(row, 4, urgency_item)
            
            # 截止日期
            deadline_item = QTableWidgetItem(task.get('deadline', '无截止日期'))
            self.table_widget.setItem(row, 5, deadline_item)
        
        # 设置表格列宽
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_widget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_widget.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table_widget)
        
        # 冲突处理策略
        strategy_layout = QHBoxLayout()
        strategy_label = QLabel("冲突处理策略:")
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "跳过重复任务",
            "替换现有任务",
            "创建新任务"
        ])
        strategy_layout.addWidget(strategy_label)
        strategy_layout.addWidget(self.strategy_combo)
        strategy_layout.addStretch()
        
        layout.addLayout(strategy_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch()
        
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def select_all(self):
        """全选所有任务"""
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, 0)
            item.setCheckState(Qt.Checked)
    
    def deselect_all(self):
        """取消全选所有任务"""
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, 0)
            item.setCheckState(Qt.Unchecked)
    
    def get_selected_strategy(self):
        """获取选中的冲突处理策略"""
        index = self.strategy_combo.currentIndex()
        strategies = ['skip', 'replace', 'create_new']
        return strategies[index]
    
    def get_selected_tasks(self):
        """获取选中的任务列表"""
        selected_tasks = []
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, 0)
            if item.checkState() == Qt.Checked:
                selected_tasks.append(self.imported_tasks[row])
        return selected_tasks