import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局字体，确保中文显示正常
    font = QFont("SimHei")
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())