import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import SettingsDialog

# 完整配置，包含所有必需的键
config = {
    "theme": 2,  # 深色主题
    "window_width": 800,
    "window_height": 600,
    "show_notifications": True,
    "update_interval": 24,  # 数据更新间隔（小时）
    "auto_backup": False,
    "backup_interval": 60,
    "backup_path": "./backups",
    "deadline_notifications": True,
    "overdue_notifications": True,
    "notification_preview": True,
    "hotkey": "<ctrl>+<alt>+t"
}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        dialog = SettingsDialog(config)
        dialog.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)