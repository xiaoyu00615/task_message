import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import SettingsDialog
from core.config_manager import ConfigManager

# 初始化配置管理器用于测试
config_manager = ConfigManager()
config = config_manager.load_config()

# 尝试初始化设置对话框，这将测试QStackedWidget是否能正常工作
print("开始测试SettingsDialog初始化...")
try:
    # 由于我们只需要测试初始化而不显示，这里不需要QApplication实例
    # 但为了完整测试，我们创建一个应用实例
    app = QApplication(sys.argv)
    
    # 创建设置对话框实例
    dialog = SettingsDialog(config)
    print("成功：SettingsDialog初始化完成，QStackedWidget正常工作！")
    
    # 直接退出，不显示窗口
    sys.exit(0)
except Exception as e:
    print(f"错误：SettingsDialog初始化失败 - {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
