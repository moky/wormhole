# -*- coding: utf-8 -*-

import time
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPalette, QTextCursor
from PyQt5.QtWidgets import QWidget, QTextEdit, QLabel, QPushButton

import dmtp

from ..client import time_string
from ..client import STUNClient, STUNClientDelegate
from ..client import DMTPClientDelegate, DMTPClient


class NATTestThread(QThread, STUNClientDelegate):

    def __init__(self, window, stun_client: STUNClient):
        super().__init__()
        self.__window = window
        stun_client.delegate = self
        self.__stun_client = stun_client

    def run(self):
        client = self.__stun_client
        address = client.server_address
        msg, res = client.get_nat_type(stun_host=address[0], stun_port=address[1])
        window = self.__window
        window.display('Detection Result: %s' % msg)
        if res is not None:
            window.display('External Address: %s' % str(res.mapped_address))
        window.update_nat(msg, res)

    #
    #   STUNClientDelegate
    #
    def feedback(self, msg: str):
        self.__window.display(message=msg)


class Window(QWidget, DMTPClientDelegate):
    update_sig = pyqtSignal(str)

    def __init__(self, dmtp_client: DMTPClient, stun_client: STUNClient):
        super().__init__(flags=Qt.WindowFlags())

        # NAT type
        label = QLabel('Please check your router type', self)
        # label.move(130, 10)
        label.setGeometry(166, 6, 400, 24)
        self.__nat = label
        # nat button
        button = QPushButton('Detect NAT type', self)
        button.clicked[bool].connect(self.test)
        button.setGeometry(10, 4, 150, 24)
        self.__test = button

        # sender
        label = QLabel('Sender:', self)
        label.move(16, 42)
        edit = QTextEdit(dmtp_client.identifier, self)
        edit.setGeometry(70, 40, 120, 24)
        self.__sender = edit
        # login button
        button = QPushButton('login', self)
        button.clicked[bool].connect(self.login)
        button.setGeometry(190, 38, 80, 24)
        self.__login = button

        # receiver
        label = QLabel('Receiver:', self)
        label.move(350, 42)
        edit = QTextEdit('hulk', self)
        edit.setGeometry(420, 40, 120, 24)
        self.__receiver = edit
        # call button
        button = QPushButton('call', self)
        button.clicked[bool].connect(self.call)
        button.setGeometry(550, 38, 80, 24)
        self.__call = button

        # input text
        edit = QTextEdit('Input text', self)
        edit.setGeometry(10, 72, 480, 30)
        self.__text = edit
        # send button
        button = QPushButton('send', self)
        button.clicked[bool].connect(self.send)
        button.setGeometry(500, 70, 130, 36)
        self.__send = button

        # info box
        box = QTextEdit('Messages:', self)
        box.setGeometry(10, 110, 620, 360)
        box.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        p: QPalette = box.palette()
        p.setColor(QPalette.Window, Qt.lightGray)
        box.setPalette(p)
        # label.setBackgroundRole(QPalette.Text)
        box.setAutoFillBackground(True)
        self.__info_box = box

        self.update_sig.connect(self.__display)

        dmtp_client.delegate = self
        stun_client.delegate = self
        self.__dmtp_client = dmtp_client
        self.__stun_client = stun_client

    @property
    def sender(self) -> str:
        return self.__sender.toPlainText()

    @property
    def receiver(self) -> str:
        return self.__receiver.toPlainText()

    @property
    def text(self) -> str:
        return self.__text.toPlainText()

    def show(self):
        self.setGeometry(10, 200, 640, 480)
        self.setMinimumSize(640, 480)
        self.setWindowTitle('P2P Chat')
        super().show()

    def __display(self, message: str):
        text = self.__info_box.toPlainText()
        if text is None:
            text = message
        else:
            text = text + '\n' + message
        self.__info_box.setText(text)
        self.__info_box.moveCursor(QTextCursor.End)

    def display(self, message: str):
        self.update_sig.emit(message)

    def test(self):
        self.__nat.setText('Detecting NAT type ...')
        t = NATTestThread(window=self, stun_client=self.__stun_client)
        t.start()

    def update_nat(self, nat: str, info):
        if nat is None:
            return
        self.__dmtp_client.nat = nat
        if info is None:
            text = '%s' % nat
        else:
            text = '%s %s' % (nat, info.mapped_address)
        self.__nat.setText(text)

    def login(self):
        self.__display('try to login: %s' % self.sender)
        self.__dmtp_client.identifier = self.sender
        self.__dmtp_client.say_hi(destination=self.__dmtp_client.server_address)

    def call(self):
        self.__display('calling: %s' % self.receiver)
        self.__dmtp_client.call(uid=self.receiver)

    def send(self) -> Optional[dmtp.Message]:
        receiver = self.receiver
        text = self.text
        msg = self.send_text(receiver=receiver, msg=text)
        if msg is None:
            self.__display('failed to send message "%s" to %s' % (text, receiver))
        else:
            when = time_string(msg.time)
            self.__display('[%s] sent to %s: "%s"' % (when, receiver, text))
        return msg

    def send_text(self, receiver: str, msg: str) -> Optional[dmtp.Message]:
        location = self.__dmtp_client.get_location(uid=receiver)
        if location is None or location.ip is None:
            print('cannot locate user: %s, %s' % (receiver, location))
            # ask the server to help building a connection
            self.__dmtp_client.call(uid=receiver)
            return None
        address = (location.ip, location.port)
        content = msg.encode('utf-8')
        msg = dmtp.Message.new(info={
            'sender': self.__dmtp_client.identifier,
            'receiver': receiver,
            'time': int(time.time()),
            'data': content,
        })
        print('sending msg to %s:\n\t%s' % (address, msg))
        self.__dmtp_client.send_message(msg=msg, destination=address)
        return msg

    #
    #   DMTPClientDelegate
    #
    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        cmd_type = cmd.type
        cmd_value = cmd.value
        if cmd_type == dmtp.Who:
            pass
        elif cmd_type == dmtp.Sign:
            assert isinstance(cmd_value, dmtp.LocationValue), 'sign cmd error: %s' % cmd_value
            message = 'punching a hole at (%s:%d) for %s' % (cmd_value.ip, cmd_value.port, cmd_value.id)
            self.display(message)
            return True
        elif cmd_type == dmtp.From:
            assert isinstance(cmd_value, dmtp.LocationValue), 'call from error: %s' % cmd_value
            message = '%s is calling from: (%s:%d)' % (cmd_value.id, cmd_value.ip, cmd_value.port)
            self.display(message)
            return True

    def process_message(self, msg: dmtp.Message, source: tuple):
        sender = msg.sender
        content = msg.content
        if content is None:
            text = ''
        else:
            text = content.decode('utf-8')
        when = time_string(msg.time)
        message = '[%s] %s %s: "%s"' % (when, source, sender, text)
        self.display(message=message)
