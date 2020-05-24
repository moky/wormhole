# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QTextCursor
from PyQt5.QtWidgets import QWidget, QTextEdit, QLabel, QPushButton

import dmtp

from ..client import ClientDelegate, Client


class Window(QWidget, ClientDelegate):
    update_sig = pyqtSignal(str)

    def __init__(self, client: Client):
        super().__init__(flags=Qt.WindowFlags())
        # sender
        label = QLabel('Sender:', self)
        label.move(10, 12)
        edit = QTextEdit(client.identifier, self)
        edit.setGeometry(60, 8, 120, 24)
        self.__sender = edit
        # login button
        button = QPushButton('login', self)
        button.clicked[bool].connect(self.login)
        button.setGeometry(180, 4, 80, 24)
        self.__login = button

        # receiver
        label = QLabel('Receiver:', self)
        label.move(350, 12)
        edit = QTextEdit('hulk', self)
        edit.setGeometry(420, 8, 120, 24)
        self.__receiver = edit
        # call button
        button = QPushButton('call', self)
        button.clicked[bool].connect(self.call)
        button.setGeometry(550, 4, 80, 24)
        self.__call = button

        # input text
        edit = QTextEdit('Input text', self)
        edit.setGeometry(10, 40, 480, 32)
        self.__text = edit
        # send button
        button = QPushButton('send', self)
        button.clicked[bool].connect(self.send)
        button.setGeometry(500, 36, 130, 40)
        self.__send = button

        # info box
        box = QTextEdit('Messages:', self)
        box.setGeometry(10, 80, 620, 390)
        box.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        p: QPalette = box.palette()
        p.setColor(QPalette.Window, Qt.lightGray)
        box.setPalette(p)
        # label.setBackgroundRole(QPalette.Text)
        box.setAutoFillBackground(True)
        self.__info_box = box

        self.update_sig.connect(self.__display)
        client.delegate = self
        self.__client = client

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
        self.setGeometry(300, 200, 640, 480)
        self.setMinimumSize(640, 480)
        self.setWindowTitle('Sechat')
        super().show()

    def __display(self, message: str):
        text = self.__info_box.toPlainText()
        if text is None:
            text = message
        else:
            text = text + '\n' + message
        # print('message text: %s' % text)
        self.__info_box.setText(text)
        self.__info_box.moveCursor(QTextCursor.End)

    def display(self, message: str):
        self.update_sig.emit(message)

    def login(self):
        self.__display('try to login: %s' % self.sender)
        self.__client.identifier = self.sender
        self.__client.say_hi(destination=self.__client.server_address)

    def call(self):
        self.__display('calling: %s' % self.receiver)
        self.__client.call(uid=self.receiver)

    def send(self):
        receiver = self.receiver
        msg = self.text
        self.__display('sending to %s: %s' % (receiver, msg))
        self.send_text(receiver=receiver, msg=msg)

    def send_text(self, receiver: str, msg: str):
        location = self.__client.get_location(uid=receiver)
        if location is None or location.ip is None:
            print('cannot locate user: %s, %s' % (receiver, location))
            # ask the server to help building a connection
            self.__client.call(uid=receiver)
            return False
        address = (location.ip, location.port)
        content = msg.encode('utf-8')
        msg = dmtp.Message.new(info={
            'sender': self.__client.identifier,
            'receiver': receiver,
            'data': content,
        })
        print('sending msg to %s:\n\t%s' % (address, msg))
        self.__client.send_message(msg=msg, destination=address)

    #
    #   ClientDelegate
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
        message = '%s %s: %s' % (source, sender, text)
        self.display(message)
