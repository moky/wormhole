/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
 *
 *                                Written in 2020 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2020 Albert Moky
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * ==============================================================================
 */
package chat.dim.dmtp.protocol;

import chat.dim.dmtp.fields.Field;
import chat.dim.dmtp.fields.FieldName;
import chat.dim.dmtp.fields.FieldValue;
import chat.dim.dmtp.values.*;

import java.net.SocketAddress;

/*     Commands
 *     ~~~~~~~~
 *
 *     WHO
 *         Ask the receiver 'Who are you?' for user ID. The receiver should respond
 *         a 'HI' command with user ID.
 *
 *     HI (HELLO)
 *         Send 'ID' to tell the receiver who you are;
 *         Send 'ID', 'ADDR', 'S' and 'NAT' to the server for login.
 *
 *         When connecting to the network, send only 'ID' to the server, if got a
 *         'SIGN' command with MAPPED-ADDRESS responds from a server, sign it and
 *         send back to the server for login.
 *
 *         Fields:
 *             ID - current user's identifier
 *             ADDR - current user's public IP and port (OPTIONAL)
 *             TIME - current time (OPTIONAL)
 *             S - signature of 'ADDR+TIME' (OPTIONAL)
 *             NAT - current user's NAT type (OPTIONAL)
 *
 *     SIGN
 *         Server-Client command: respond the user's MAPPED-ADDRESS to ask signing.
 *
 *         Fields:
 *             ID - user identifier
 *             ADDR - user's public IP and port
 *
 *     CALL
 *         Client-Server command: ask the server to help connecting with someone.
 *
 *         Field:
 *             ID - contact identifier
 *
 *     FROM
 *         Server-Client command: deliver the user's location info;
 *         When the server received a 'CALL' command from user(A), it will check
 *         whether another user(B) being called is online,
 *         if YES, send a 'FROM' command to user(B) with the user(A)'s location,
 *         at the same time, respond to user(A) with the user(B)'s location;
 *         if NO, respond an empty 'FROM' command with only one field 'ID'.
 *
 *         Fields:
 *             ID - user identifier
 *             ADDR - user's public IP and port (OPTIONAL)
 *             TIME - signed time (OPTIONAL)
 *             S - signature of 'ADDR+TIME' signed by this user (OPTIONAL)
 *             NAT - user's NAT type (OPTIONAL)
 *
 *     BYE
 *         When a client is offline, send this command to the server, or broadcast
 *         this command to every contacts to logout.
 *
 *         Fields:
 *             ID - user identifier
 *             ADDR - user's public IP and port
 *             TIME - signed time
 *             S - signature of 'ADDR+TIME' signed by this user
 *             NAT - user's NAT type (OPTIONAL)
 */

public class Command extends Field {

    public Command(byte[] data, FieldName type, FieldValue value) {
        super(data, type, value);
    }

    public Command(FieldName type, FieldValue value) {
        super(type, value);
    }

    //
    //  Commands
    //

    public static class Who extends Command {

        public Who(byte[] data) {
            super(data, WHO, null);
        }

        public Who() {
            super(WHO, null);
        }

        public static Who create() {
            return new Who();
        }
    }

    public static class Hello extends Command {

        public Hello(byte[] data, FieldValue value) {
            super(data, HELLO, value);
        }

        public Hello(FieldValue value) {
            super(HELLO, value);
        }

        //
        //  Factories
        //

        public static Hello create(LocationValue locationValue) {
            return new Hello(locationValue);
        }

        public static Hello create(StringValue identifier,
                                   SourceAddressValue sourceAddress,
                                   MappedAddressValue mappedAddress,
                                   RelayedAddressValue relayedAddress,
                                   TimestampValue timestamp,
                                   BinaryValue signature,
                                   StringValue nat) {
            return create(LocationValue.create(identifier,
                    sourceAddress, mappedAddress, relayedAddress,
                    timestamp, signature, nat));
        }

        public static Hello create(String identifier,
                                   SocketAddress sourceAddress,
                                   SocketAddress mappedAddress,
                                   SocketAddress relayedAddress,
                                   long timestamp,
                                   byte[] signature,
                                   String nat) {
            return create(LocationValue.create(identifier,
                    sourceAddress, mappedAddress, relayedAddress,
                    timestamp, signature, nat));
        }

        public static Hello create(StringValue identifier) {
            return create(identifier, null, null, null,
                    null, null, null);
        }

        public static Hello create(String identifier) {
            return create(identifier, null, null, null,
                    0, null, null);
        }
    }

    public static class Sign extends Command {

        public Sign(byte[] data, FieldValue value) {
            super(data, SIGN, value);
        }

        public Sign(FieldValue value) {
            super(SIGN, value);
        }

        //
        //  Factories
        //

        public static Sign create(LocationValue locationValue) {
            return new Sign(locationValue);
        }

        public static Sign create(StringValue identifier,
                                  MappedAddressValue mappedAddress,
                                  RelayedAddressValue relayedAddress) {
            return create(LocationValue.create(identifier,
                    null, mappedAddress, relayedAddress));
        }

        public static Sign create(String identifier,
                                  SocketAddress mappedAddress,
                                  SocketAddress relayedAddress) {
            return create(LocationValue.create(identifier,
                    null, mappedAddress, relayedAddress));
        }
    }

    public static class Call extends Command {

        public Call(byte[] data, FieldValue value) {
            super(data, CALL, value);
        }

        public Call(FieldValue value) {
            super(CALL, value);
        }

        //
        //  Factories
        //

        public static Call create(LocationValue locationValue) {
            return new Call(locationValue);
        }

        public static Call create(StringValue identifier) {
            return create(LocationValue.create(identifier));
        }

        public static Call create(String identifier) {
            return create(LocationValue.create(identifier));
        }
    }

    public static class From extends Command {

        public From(byte[] data, FieldValue value) {
            super(data, FROM, value);
        }

        public From(FieldValue value) {
            super(FROM, value);
        }

        //
        //  Factories
        //

        public static From create(LocationValue locationValue) {
            return new From(locationValue);
        }

        public static From create(StringValue identifier) {
            return create(LocationValue.create(identifier));
        }

        public static From create(String identifier) {
            return create(LocationValue.create(identifier));
        }
    }

    public static class Bye extends Command {

        public Bye(byte[] data, FieldValue value) {
            super(data, BYE, value);
        }

        public Bye(FieldValue value) {
            super(BYE, value);
        }

        //
        //  Factories
        //

        public static Bye create(LocationValue locationValue) {
            return new Bye(locationValue);
        }
    }

    //
    //  Command names
    //

    public static final FieldName WHO   = new FieldName("WHO");   // (S) location not found, ask receiver to say 'HI'
    public static final FieldName HELLO = new FieldName("HI");    // (C) login with ID
    public static final FieldName SIGN  = new FieldName("SIGN");  // (S) ask client to login
    public static final FieldName CALL  = new FieldName("CALL");  // (C) ask server to help connecting with another user
    public static final FieldName FROM  = new FieldName("FROM");  // (S) help users connecting
    public static final FieldName BYE   = new FieldName("BYE");   // (C) logout with ID and address

    static {
        FieldValue.register(HELLO, LocationValue.class);
        FieldValue.register(SIGN, LocationValue.class);
        FieldValue.register(CALL, CommandValue.class);
        FieldValue.register(FROM, LocationValue.class);
        FieldValue.register(BYE, LocationValue.class);
    }
}
