import sys
import socket
from utils import *
import numpy as np 
import threading
import stopThreading
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import tcp_logic


class MainWin(tcp_logic.TcpLogic):
    # 信号槽机制：设置一个信号，用于触发接收区写入动作
    signal_write_msg = pyqtSignal(str)
    signal_plot = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client_th = None
        self.plot_th = None
        self.trigger_mod = 0  # 触发模式，默认0为内触发，1为外触发
        self.code = b'\xab\x1b\x00\x02\x00\x00\x00\xab'  # 给下位机发送的指令
        self.rec_buff = b''  # 网口上一次接收数据的残余缓存（外触发模式）
        self.data_len = 20  #一次接收的绘图数据的大小
        self.reset(0)
        self.connect_slots()
        
    def connect_slots(self):
        self.signal_write_msg.connect(self.write_msg)
        self.signal_plot.connect(self.update_plot)

    @pyqtSlot()
    def on_getLocalPB_clicked(self):
        """
        getLocalPB控件点击触发的槽
        :return: None
        """
        # 获取本机ip
        self.local_ip_LE.clear()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            my_addr = s.getsockname()[0]
            self.local_ip_LE.setText(str(my_addr))
        except:
            # 若无法连接互联网使用，会调用以下方法
            try:
                my_addr = socket.gethostbyname(socket.gethostname())
                self.local_ip_LE.setText(str(my_addr))
            except:
                self.signal_write_msg.emit("无法获取ip，请连接网络！\n")
        finally:
            s.close()
    
    @pyqtSlot()
    def on_connectPB_clicked(self):
        """
        connectPB控件点击触发的槽
        :return: None
        """
        if self.tcp_client_start():
            self.reset(1)

    @pyqtSlot()
    def on_discPB_clicked(self):
        """
        discPB控件点击触发的槽
        :return: None
        """
        # 关闭连接
        self.on_stopPB_clicked()
        self.tcp_close()
        self.reset(0)

    @pyqtSlot()
    def on_recPB_clicked(self):
        mod = self.trigger_mod
        code_arr = np.asarray(bytearray(self.code))
        if mod == 0:  # 内触发需要先发送开始指令才能产生数据流
            try:
                t = int(self.timeLE.text())
            except:
                self.signal_write_msg.emit('数据格式错误！')
                return 0
            time_mod = self.timeModCB.currentIndex()
            if time_mod == 0 and (t>=0 and t<100):
                pass
            elif time_mod == 1 and (t>=100 and t<6e6):
                t = int(t/100)
            else:
                self.signal_write_msg.emit('请检查输入数据范围！')
                return 0
            code_arr[2] = t&0xff00
            code_arr[3] = t&0x00ff
            code_arr[4] = time_mod
            self.code = bytes(code_arr)    
            self.tcp_send(self.code)
        if self.client_th is None:  # 避免重复创建线程
            self.client_th = threading.Thread(target=self.tcp_client_concurrency,args=(mod,))
            self.client_th.start()
            self.stopPB.setEnabled(True)
            if mod != 0:
                self.recPB.setEnabled(False)
        self.trigModCB.setEnabled(False)

    @pyqtSlot()
    def on_stopPB_clicked(self):
        try:
            stopThreading.stop_thread(self.client_th)
        except:
            pass
        else:
            self.client_th = None
            self.recPB.setEnabled(True)
            self.stopPB.setEnabled(False)
            self.trigModCB.setEnabled(True)

    @pyqtSlot()
    def on_sendPB_clicked(self):
        if self.link is True:
            str_data = self.sendTE.toPlainText()
            if self.hexCKB.isChecked():
                data = hexStringTobytes(str_data)
                if data == 0:
                    self.signal_write_msg.emit('数据格式错误！')
                    return 0
            else:
                data = stringTobytes(str_data)
            self.tcp_send(data)

    @pyqtSlot(int)
    def on_trigModCB_currentIndexChanged(self,index):
        self.trigger_mod = index
        if index == 1:  # 外触发
            self.timeLE.hide()
            self.timeModCB.hide()
            self.timeLabel.hide()
            self.sendTE.hide()
            self.hexCKB.hide()
            self.sendPB.hide()
        elif index ==0 :
            self.timeLE.show()
            self.timeModCB.show()
            self.timeLabel.show()
            self.sendTE.hide()
            self.hexCKB.hide()
            self.sendPB.hide()
        elif index ==2 :
            self.timeLE.hide()
            self.timeModCB.hide()
            self.timeLabel.hide()
            self.sendTE.show()
            self.hexCKB.show()
            self.sendPB.show()

    def update_plot(self, ydata):
        if self.plot_th is None:
            self.plot_th = self.plotView.plotItem.plot()
        self.plot_th.setData(y=ydata)

    def tcp_client_concurrency(self, mod):
        """
        功能函数，用于TCP客户端创建子线程的方法，阻塞式接收
        :return:
        """
        while True:
            recv_msg = self.tcp_socket.recv(20480)
            self.signal_write_msg.emit('接收数据量：'+str(len(recv_msg))+' 字节\n')
            if recv_msg:
                if mod != 2:    # 内触发模式，8个字节的确认信息+20000个字节的数据
                    if mod == 0 and len(recv_msg)==(self.data_len+8):
                        data = np.asarray(bytearray(recv_msg))
                        ydata = self.byte_shift(np.asarray(data[8:(self.data_len+8)]).reshape([int(self.data_len/2),2]))
                        print(str(ydata))
                        self.signal_plot.emit(ydata[:,0])
                    elif mod == 1:
                        data = np.asarray(bytearray(self.rec_buff + recv_msg))
                        for i in range(int(len(data)/self.data_len)):
                            ydata = self.byte_shift(np.asarray(data[0:self.data_len]).reshape([int(self.data_len/2),2]))
                            self.signal_plot.emit(ydata[:,0])
                            data = data[self.data_len:]
                            self.rec_buff = bytes(data)  
                else:
                    if self.hexCKB.isChecked():
                        self.signal_write_msg.emit(bytesToHexString(recv_msg)+'\n')
                    else:
                        self.signal_write_msg.emit(str(recv_msg.decode('utf-8'))+'\n')
            else:
                self.tcp_socket.close()
                self.reset(0)
                msg = '从服务器断开连接\n'
                self.signal_write_msg.emit(msg)
                break

    def byte_shift(self,data):
        '''
        data为N*M的数组dec list，每个元素代表一个字节，
        将每M个字节拼接形成一个新数据，返回N*1数组
        '''
        out = np.zeros([len(data), 1])
        for i in range(len(data)):    # convert the hex data from serial into dec list
            for j in range(len(data[i])):
                out[i] = out[i] + (data[i, len(data[i])-j-1] << j*8)
        return out
        
    def write_msg(self, msg):
        # signal_write_msg信号会触发这个函数
        """
        功能函数，向接收区写入数据的方法
        信号-槽触发
        tip：PyQt程序的子线程中，直接向主线程的界面传输字符是不符合安全原则的
        :return: None
        """
        self.msgTB.insertPlainText(msg)
        # 滚动条移动到结尾
        self.msgTB.moveCursor(QTextCursor.End)

    def reset(self,state):
        """
        功能函数，根据state参数，设置按钮状态
        state: 0 重置初始化，1 设置为连接状态
        :return:None
        """
        self.stateLed.set_state(state)
        flag = bool(state)
        self.link = flag
        self.connectPB.setEnabled(not flag)
        self.discPB.setEnabled(flag)
        self.recPB.setEnabled(flag)
        self.stopPB.setEnabled(False)
        self.sendPB.setEnabled(flag)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MainWin()
    myWin.show()
    sys.exit(app.exec_())