print('测试定时器功能中...')
import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, QDateTime, QEventLoop

# 测试定时器功能
def test_timer():
    print('定时器测试开始')
    
    app = QApplication(sys.argv)
    
    # 创建一个简单的窗口
    window = QWidget()
    
    # 创建定时器
    timer = QTimer()
    
    # 设置计数器
    counter = 0
    
    # 定义槽函数
    def timer_timeout():
        nonlocal counter
        counter += 1
        now = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
        print(f'定时器触发 {counter} 次，当前时间: {now}')
    
    # 连接信号
    timer.timeout.connect(timer_timeout)
    
    # 设置间隔为1秒
    timer.setInterval(1000)
    
    # 启动定时器
    timer.start()
    print('定时器已启动，间隔1秒')
    
    # 使用QEventLoop来等待，不阻塞事件循环
    loop = QEventLoop()
    QTimer.singleShot(3000, loop.quit)  # 3秒后退出循环
    loop.exec_()
    
    # 停止定时器
    timer.stop()
    print('定时器已停止')
    print(f'预期触发次数: 2-3次，实际触发次数: {counter}')
    
    return counter > 0

result = test_timer()
print(f'测试结果: {'成功' if result else '失败'}')

sys.exit(0 if result else 1)