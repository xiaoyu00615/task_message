import sys
from PyQt5.QtWidgets import QApplication

try:
    print("测试QApplication导入...")
    print(f"QApplication已成功导入: {QApplication}")
    print("测试成功！")
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()
