# 任务管理应用 (Tasks Message)

一个简洁高效的跨平台任务管理工具，帮助用户管理日常待办事项，支持PC端（PyQt5）和手机端（Kivy），并实现了局域网内的数据同步功能。

## 功能特性

### 核心功能
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

### 跨端同步功能
- ✅ PC端和手机端双向增量同步
- ✅ 基于HTTP协议的局域网通信
- ✅ 后台自动同步（可配置同步间隔）
- ✅ 断网时本地缓存，联网后自动同步

### 手机端特性
- ✅ 基于Kivy框架的原生UI
- ✅ 适配手机屏幕尺寸
- ✅ 支持横竖屏显示
- ✅ 可打包为Android APK

## 技术栈

### PC端
- **语言**：Python 3
- **GUI框架**：PyQt5
- **数据存储**：SQLite + JSON
- **通信方式**：Flask HTTP服务器

### 手机端
- **语言**：Python 3
- **GUI框架**：Kivy 2.3.1
- **数据存储**：SQLite
- **通信方式**：HTTP请求
- **打包工具**：Buildozer (WSL环境)

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
pip install pyqt5 flask kivy requests
```

### 运行应用

#### PC端
```bash
# 运行PC端主程序
python main.py

# 启动PC端同步服务器
python pc_server.py
```

#### 手机端（PC测试）
```bash
python phone_main.py
```

#### 手机端（Android APK）
请参考`APK_PACKAGING_GUIDE.md`文档，了解如何在Windows系统下使用WSL+Buildozer打包APK。

## 项目结构

```
tasks_message/
├── main.py                     # PC端主程序入口
├── phone_main.py               # 手机端主程序入口
├── pc_server.py                # PC端Flask服务器（用于数据同步）
├── core/              # 核心逻辑模块
│   ├── __init__.py
│   ├── config_manager.py  # 配置管理
│   ├── data_manager.py    # 数据管理
│   ├── sqlite_manager.py  # SQLite数据库管理
│   ├── task_handler.py    # 任务处理逻辑
│   └── json_utils.py      # JSON文件操作工具
├── ui/                # 用户界面模块
│   ├── __init__.py
│   ├── main_window.py     # 主窗口
│   └── widgets.py         # 自定义控件
├── phone_ui.py         # 手机端UI界面
├── phone_data.py       # 手机端数据管理
├── phone_network.py    # 手机端网络通信
├── data/              # 数据存储目录
│   └── tasks.json     # 任务数据文件（JSON格式）
├── config.json        # 配置文件
└── README.md          # 项目说明文档
```

## 数据同步使用方法

### 1. 启动PC端同步服务器

首先需要启动PC端的同步服务器，用于接收手机端的连接和数据同步请求：

```bash
python pc_server.py
```

服务器默认在`0.0.0.0:5000`端口监听。

### 2. 配置手机端连接

1. 在手机端应用中，点击右上角的设置按钮
2. 选择"连接设置"
3. 输入PC端的IP地址（或点击"扫描局域网PC"自动搜索）
4. 点击"确定"完成配置

### 3. 数据同步

配置完成后，手机端会自动与PC端进行数据同步：

- 后台每30秒自动同步一次
- 可以手动点击"同步"按钮立即同步
- 断网时自动缓存，联网后自动同步

## 调试工具

项目包含几个用于调试的脚本：

- **debug_urgency.py**：调试紧急度计算逻辑
- **test_fix.py**：测试紧急度修复效果
- **test_promote.py**：测试紧急度升级功能
- **update_test_task.py**：更新测试任务

## 快捷键

- **Ctrl+Alt+T**：显示/隐藏主窗口

## 注意事项

1. 确保PC端和手机端处于同一局域网内
2. PC端需要关闭防火墙或允许5000端口的连接
3. 首次使用时，建议先在PC端创建一些任务进行测试
4. 打包APK时需要确保WSL环境配置正确

## 许可证

MIT License