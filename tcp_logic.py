import socket
import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from myui.MainUi import Ui_MainWindow
import pyqtgraph as pg

class TcpLogic(QMainWindow,Ui_MainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUi()
        self.tcp_socket = None
        self.link = False  # 用于标记是否开启了连接
        
    def initUi(self):
        pg.setConfigOption('background', 'w')
        QApplication.setStyle('fusion')
        self.setupUi(self)
        self.sendTE.hide()
        self.hexCKB.hide()
        self.sendPB.hide()
        # 获取显示器分辨率大小
        desktop = QApplication.desktop()
        screenRect = desktop.screenGeometry()
        h = screenRect.height()
        w = screenRect.width()
        self.setGeometry(int(w*0.1), int(h*0.1), int(w*0.8), int(h*0.8))

    def tcp_client_start(self):
        """
        功能函数，TCP客户端连接其他服务端的方法
        :return: 0 连接失败，1 连接成功
        """
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            address = (str(self.des_ip_LE.text()), int(self.portLE.text()))
        except Exception as ret:
            msg = '请检查目标IP，目标端口\n'
            self.signal_write_msg.emit(msg)
            return 0
        else:
            try:
                msg = '正在连接目标服务器\n'
                self.signal_write_msg.emit(msg)
                self.tcp_socket.connect(address)
            except Exception as ret:
                msg = '无法连接目标服务器\n'
                self.signal_write_msg.emit(msg)
                return 0
            else:
                msg = 'TCP客户端已连接IP:%s端口:%s\n' % address
                self.signal_write_msg.emit(msg)
                return 1

    def tcp_send(self,msg_send):
        """
        功能函数，用于TCP服务端和TCP客户端发送消息
        msg_send: 需要发送的bytes数据
        :return: None
        """
        if self.link is False:
            msg = '请选择服务，并点击连接网络\n'
            self.signal_write_msg.emit(msg)
        else:
            try:
                self.tcp_socket.send(msg_send)
                msg = 'TCP客户端已发送\n'
                self.signal_write_msg.emit(msg)
            except Exception as ret:
                msg = '发送失败\n'
                self.signal_write_msg.emit(msg)

    def tcp_close(self):
        """
        功能函数，关闭网络连接的方法
        :return:
        """
        try:
            self.tcp_socket.close()
            if self.link is True:
                msg = '已断开网络\n'
                self.signal_write_msg.emit(msg)
        except Exception as ret:
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = TcpLogic()
    ui.show()
    sys.exit(app.exec_())
