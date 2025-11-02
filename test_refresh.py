import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer
import time

def test_refresh_logic():
    try:
        app = QApplication(sys.argv)
        
        # 模拟refresh_time_display中的QApplication使用
        print("测试QApplication静态方法调用...")
        
        # 测试鼠标按钮检查
        mouse_buttons = QApplication.mouseButtons()
        print(f"鼠标按钮状态: {mouse_buttons}, Qt.NoButton: {Qt.NoButton}")
        print(f"是否相等: {mouse_buttons == Qt.NoButton}")
        
        # 测试键盘修饰键检查
        modifiers = QApplication.keyboardModifiers()
        print(f"键盘修饰键状态: {modifiers}, Qt.NoModifier: {Qt.NoModifier}")
        print(f"是否相等: {modifiers == Qt.NoModifier}")
        
        print("测试成功完成！")
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_refresh_logic()
