# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

import threading
import time
from typing import Optional
from weakref import WeakValueDictionary

from dmtp import LocationValue, SourceAddressValue, TimestampValue
from dmtp import ContactDelegate, Contact


class Session:

    def __init__(self, location: LocationValue, address: tuple):
        super().__init__()
        self.__location = location
        self.__address = address

    @property
    def location(self) -> LocationValue:
        return self.__location

    @property
    def address(self) -> tuple:
        return self.__address


class ContactManager(ContactDelegate):

    def __init__(self):
        super().__init__()
        self.identifier: str = None
        self.source_address: tuple = None
        self.nat: str = 'Unknown'
        # contacts
        self.__contacts = {}  # ID -> Contact
        self.__contacts_lock = threading.Lock()
        self.__locations = WeakValueDictionary()  # (IP, port) -> LocationValue

    def verify_location(self, location: LocationValue) -> bool:
        if location is None \
                or location.identifier is None \
                or location.mapped_address is None \
                or location.signature is None:
            # location error
            return False
        with self.__contacts_lock:
            contact = self.__contacts.get(location.identifier)
        if contact is None:
            return False
        # data = "source_address" + "mapped_address" + "relayed_address" + "time"
        data = location.mapped_address.data
        if location.source_address is not None:
            data = location.source_address.data + data
        if location.relayed_address is not None:
            data = data + location.relayed_address.data
        timestamp = TimestampValue(value=location.timestamp)
        data += timestamp.data
        signature = location.signature
        # TODO: verify data and signature with public key
        assert data is not None and signature is not None
        return True

    def sign_location(self, location: LocationValue) -> Optional[LocationValue]:
        identifier = self.identifier
        if location.identifier != identifier:
            return None
        # sign(source_address + mapped_address + relayed_address + timestamp)
        mapped_address = location.mapped_address
        data = mapped_address.data
        # source address
        source_ip = self.source_address[0]
        source_port = self.source_address[1]
        source_address = SourceAddressValue(ip=source_ip, port=source_port)
        data = source_address.data + data
        # relayed address
        if location.relayed_address is None:
            relayed_address = None
        else:
            relayed_address = location.relayed_address
            data = data + relayed_address.data
        # time
        timestamp = int(time.time())
        data += TimestampValue(value=timestamp).data
        # TODO: sign it with private key
        signature = b'sign(' + data + b')'
        return LocationValue.new(identifier=identifier,
                                 source_address=source_address,
                                 mapped_address=mapped_address,
                                 relayed_address=relayed_address,
                                 timestamp=timestamp, signature=signature, nat=self.nat)

    def current_location(self) -> LocationValue:
        locations = self.get_locations(identifier=self.identifier)
        host = self.source_address[0]
        port = self.source_address[1]
        for loc in locations:
            assert isinstance(loc, LocationValue), 'location error: %s' % loc
            if loc.source_address is not None \
                    and port == loc.source_address.port and host == loc.source_address.ip:
                return loc

    def get_location(self, address: tuple) -> Optional[LocationValue]:
        return self.__locations.get(address)

    def get_locations(self, identifier: str) -> list:
        with self.__contacts_lock:
            contact = self.__contacts.get(identifier)
            if contact is None:
                return []
            assert isinstance(contact, Contact), 'contact error: %s' % contact
            return contact.locations

    def update_location(self, location: LocationValue) -> bool:
        identifier = location.identifier
        # TODO: verify signature
        # set with contact
        with self.__contacts_lock:
            contact = self.__contacts.get(identifier)
            if contact is None:
                # create new contact
                contact = Contact(identifier=identifier)
                self.__contacts[identifier] = contact
            # update location for this contact
            if not contact.update_location(location=location):
                return False
        # set with source address
        address = location.source_address
        if address is not None:
            address = (address.ip, address.port)
            self.__locations[address] = location
        # set with mapped address
        address = location.mapped_address
        if address is not None:
            address = (address.ip, address.port)
            self.__locations[address] = location
        return True

    def remove_location(self, location: LocationValue) -> bool:
        identifier = location.identifier
        # TODO: verify signature
        # remove with source address
        address = location.source_address
        if address is not None:
            address = (address.ip, address.port)
            self.__locations.pop(address)
        # remove with mapped address
        address = location.mapped_address
        if address is not None:
            address = (address.ip, address.port)
            self.__locations.pop(address)
        # remove with contact
        with self.__contacts_lock:
            contact = self.__contacts.get(identifier)
            if contact is None:
                return False
            assert isinstance(contact, Contact), 'contact error: %s' % contact
            return contact.remove_location(location=location)
