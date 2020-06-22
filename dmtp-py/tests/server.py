#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from typing import Optional
from weakref import WeakValueDictionary

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import dmtp


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9395


class Server(dmtp.Server):

    def __init__(self, port: int, host: str='127.0.0.1'):
        super().__init__(host=host, port=port)
        # online contacts
        self.__contacts: dict = {}          # ID -> Contact
        self.__map = WeakValueDictionary()  # (IP, port) -> Contact

    #
    #   Contacts (with locations)
    #

    def get_contact(self, identifier: str=None, address: tuple=None) -> Optional[dmtp.Contact]:
        """ get contact by ID or address """
        if identifier is None:
            assert len(address) == 2, 'address error: %s' % str(address)
            return self.__map.get(address)
        else:
            return self.__contacts.get(identifier)

    def set_location(self, location: dmtp.LocationValue) -> bool:
        """ Login """
        if self.__analyze_location(location=location) < 0:
            print('location error: %s' % location)
            return False
        identifier = location.identifier
        contact = self.get_contact(identifier=identifier)
        if contact is None:
            contact = self._create_contact(identifier=identifier)
        if contact.update_location(location=location):
            self.__contacts[identifier] = contact
            return True

    def remove_location(self, location: dmtp.LocationValue) -> bool:
        """ Logout """
        identifier = location.identifier
        contact = self.get_contact(identifier=identifier)
        if contact is None:
            return False
        assert isinstance(contact, dmtp.Contact), 'contact error: %s' % contact
        if contact.remove_location(location=location):
            if not contact.is_online:
                # all sessions removed/expired
                self.__contacts.pop(identifier, None)
            if location.source_address is not None:
                address = location.source_address
                address = (address.ip, address.port)
                self.__map.pop(address, None)
            if location.mapped_address is not None:
                address = location.mapped_address
                address = (address.ip, address.port)
                self.__map.pop(address, None)
            return True

    def update_address(self, address: tuple, contact: dmtp.Contact) -> bool:
        if contact.update_address(address=address):
            self.__map[address] = contact
            return True

    # noinspection PyMethodMayBeStatic
    def __analyze_location(self, location: dmtp.LocationValue) -> int:
        if location is None:
            # location should not empty
            return -1
        if location.identifier is None:
            # user ID should not empty
            return -2
        if location.mapped_address is None:
            # mapped address should not empty
            return -3
        if location.signature is None:
            # location not signed
            return -4
        # data = "source_address" + "mapped_address" + "relayed_address" + "time"
        data = location.mapped_address.data
        if location.source_address is not None:
            data = location.source_address.data + data
        if location.relayed_address is not None:
            data = data + location.relayed_address.data
        timestamp = dmtp.TimestampValue(value=location.timestamp)
        data += timestamp.data
        signature = location.signature
        # TODO: verify data and signature with public key
        assert data is not None and signature is not None
        return 0

    def say_hi(self, destination: tuple) -> bool:
        cmd = dmtp.HelloCommand.new(identifier='station@anywhere')
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        return True

    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        print('received cmd: %s' % cmd)
        return super().process_command(cmd=cmd, source=source)

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg: %s' % msg)
        return True


if __name__ == '__main__':
    # create server
    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))
    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)
    g_server.start()
