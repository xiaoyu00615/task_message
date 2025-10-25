# 任务管理应用 (Tasks Message)

一个简洁高效的任务管理工具，帮助用户管理日常待办事项，支持任务的添加、标记完成、删除以及基于截止日期的自动紧急度管理。

## 功能特性

- **任务管理**：添加、标记完成、删除任务
- **优先级设置**：支持设置任务重要度（1-3星）和紧急度（1-5级）
- **截止日期**：可为任务设置截止日期，支持"一周后"快速设置
- **自动紧急度管理**：根据剩余时间自动调整任务紧急度
  - 7天以上：紧急度5级（最不紧急）
  - 3-7天：紧急度4级（较不紧急）
  - 1-3天：紧急度3级（中等）
  - 1天内：紧急度2级（紧急）
  - 已过期：紧急度1级（最紧急）
- **系统托盘通知**：任务添加和紧急度变化时显示通知
- **任务排序**：按紧急度和重要度智能排序
- **超时管理**：自动将过期任务移至超时列表

## 技术栈

- **语言**：Python 3
- **GUI框架**：PyQt5
- **数据存储**：JSON文件

## 快速开始

### 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

# 安装依赖
pip install pyqt5
```

### 运行应用

```bash
python main.py
```

## 项目结构

```
tasks_message/
├── core/              # 核心逻辑模块
│   ├── __init__.py
│   ├── config_manager.py  # 配置管理
│   ├── data_manager.py    # 数据管理
│   └── task_handler.py    # 任务处理逻辑
├── ui/                # 用户界面模块
│   ├── __init__.py
│   ├── main_window.py     # 主窗口
│   └── widgets.py         # 自定义控件
├── main.py            # 应用入口
├── config.json        # 配置文件
├── tasks.json         # 任务数据文件
└── README.md          # 项目说明文档
```

## 调试工具

项目包含几个用于调试的脚本：

- **debug_urgency.py**：调试紧急度计算逻辑
- **test_fix.py**：测试紧急度修复效果
- **test_promote.py**：测试紧急度升级功能
- **update_test_task.py**：更新测试任务

## 快捷键

- **Ctrl+Alt+T**：显示/隐藏主窗口
