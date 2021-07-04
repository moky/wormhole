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

import java.net.SocketAddress;
import java.util.List;

import chat.dim.stun.valus.MappedAddressValue;
import chat.dim.stun.valus.SourceAddressValue;
import chat.dim.tlv.Entry;
import chat.dim.tlv.Field;
import chat.dim.tlv.FieldParser;
import chat.dim.tlv.Value;
import chat.dim.tlv.lengths.VarLength;
import chat.dim.tlv.tags.StringTag;
import chat.dim.tlv.values.RawValue;
import chat.dim.tlv.values.StringValue;
import chat.dim.tlv.values.Value32;
import chat.dim.turn.values.RelayedAddressValue;
import chat.dim.type.ByteArray;

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

    public Command(Entry<StringTag, VarLength, Value> tlv) {
        super(tlv);
    }

    public Command(ByteArray data, StringTag type, VarLength length, Value value) {
        super(data, type, length, value);
    }

    //
    //  Factories
    //

    public static Command createCommand(StringTag tag, VarLength length, Value value) {
        if (value == null) {
            value = RawValue.ZERO;
            length = VarLength.ZERO;
        } else if (length == null) {
            length = VarLength.from(value.getSize());
        }
        return new Command(tag.concat(length, value), tag, length, value);
    }
    public static Command createCommand(StringTag tag, Value value) {
        return createCommand(tag, null, value);
    }
    public static Command createCommand(StringTag tag) {
        return createCommand(tag, null, null);
    }

    //
    //  Who
    //
    public static Command createWhoCommand() {
        return createCommand(WHO);
    }

    //
    //  Hello
    //
    public static Command createHelloCommand(LocationValue locationValue) {
        return createCommand(HELLO, locationValue);
    }
    public static Command createHelloCommand(StringValue identifier,
                                             SourceAddressValue sourceAddress,
                                             MappedAddressValue mappedAddress,
                                             RelayedAddressValue relayedAddress,
                                             Value32 timestamp,
                                             RawValue signature,
                                             StringValue nat) {
        return createCommand(HELLO, LocationValue.create(identifier,
                sourceAddress, mappedAddress, relayedAddress,
                timestamp, signature, nat));
    }
    public static Command createHelloCommand(String identifier,
                               SocketAddress sourceAddress,
                               SocketAddress mappedAddress,
                               SocketAddress relayedAddress,
                               long timestamp,
                               ByteArray signature,
                               String nat) {
        return createCommand(HELLO, LocationValue.create(identifier,
                sourceAddress, mappedAddress, relayedAddress,
                timestamp, signature, nat));
    }
    public static Command createHelloCommand(StringValue identifier) {
        return createHelloCommand(identifier, null, null, null,
                null, null, null);
    }
    public static Command createHelloCommand(String identifier) {
        return createHelloCommand(identifier, null, null, null,
                0, null, null);
    }

    //
    //  Sign
    //
    public static Command createSignCommand(LocationValue locationValue) {
        return createCommand(SIGN, locationValue);
    }
    public static Command createSignCommand(StringValue identifier,
                              MappedAddressValue mappedAddress,
                              RelayedAddressValue relayedAddress) {
        return createCommand(SIGN, LocationValue.create(identifier,
                null, mappedAddress, relayedAddress));
    }

    public static Command createSignCommand(String identifier,
                              SocketAddress mappedAddress,
                              SocketAddress relayedAddress) {
        return createCommand(SIGN, LocationValue.create(identifier,
                null, mappedAddress, relayedAddress));
    }

    //
    //  Call
    //
    public static Command createCallCommand(LocationValue locationValue) {
        return createCommand(CALL, locationValue);
    }

    public static Command createCallCommand(StringValue identifier) {
        return createCommand(CALL, LocationValue.create(identifier));
    }

    public static Command createCallCommand(String identifier) {
        return createCommand(CALL, LocationValue.create(identifier));
    }

    //
    //  From
    //
    public static Command createFromCommand(LocationValue locationValue) {
        return createCommand(FROM, locationValue);
    }

    public static Command createFromCommand(StringValue identifier) {
        return createCommand(FROM, LocationValue.create(identifier));
    }

    public static Command createFromCommand(String identifier) {
        return createCommand(FROM, LocationValue.create(identifier));
    }

    //
    //  Bye
    //
    public static Command createByeCommand(LocationValue locationValue) {
        return createCommand(BYE, locationValue);
    }

    //
    //  Parser
    //
    private static final FieldParser<Command> parser = new FieldParser<Command>() {
        @Override
        protected Command createEntry(ByteArray data, StringTag type, VarLength length, Value value) {
            return new Command(data, type, length, value);
        }
    };

    public static List<Command> parseCommands(ByteArray data) {
        return parser.parseEntries(data);
    }

    //
    //  Field names
    //

    public static final StringTag ID              = StringTag.from("ID");    // user ID
    public static final StringTag SOURCE_ADDRESS  = StringTag.from("SOURCE-ADDRESS");
    public static final StringTag MAPPED_ADDRESS  = StringTag.from("MAPPED-ADDRESS");
    public static final StringTag RELAYED_ADDRESS = StringTag.from("RELAYED-ADDRESS");
    public static final StringTag TIME            = StringTag.from("TIME");  // timestamp (uint32, big endian)
    public static final StringTag SIGNATURE       = StringTag.from("SIGNATURE");
    public static final StringTag NAT             = StringTag.from("NAT");   // NAT type

    static {
        register(ID,              StringValue::parse);
        register(SOURCE_ADDRESS,  SourceAddressValue::parse);
        register(MAPPED_ADDRESS,  MappedAddressValue::parse);
        register(RELAYED_ADDRESS, RelayedAddressValue::parse);
        register(TIME,            Value32::parse);
        register(SIGNATURE,       RawValue::parse);
        register(NAT,             StringValue::parse);
    }

    //
    //  Command names
    //

    public static final StringTag WHO   = StringTag.from("WHO");   // (S) location not found, ask receiver to say 'HI'
    public static final StringTag HELLO = StringTag.from("HI");    // (C) login with ID
    public static final StringTag SIGN  = StringTag.from("SIGN");  // (S) ask client to login
    public static final StringTag CALL  = StringTag.from("CALL");  // (C) ask server to help connecting with another user
    public static final StringTag FROM  = StringTag.from("FROM");  // (S) help users connecting
    public static final StringTag BYE   = StringTag.from("BYE");   // (C) logout with ID and address

    static {
        register(HELLO, LocationValue::parse);
        register(SIGN,  LocationValue::parse);
        register(CALL,  CommandValue::parse);
        register(FROM,  LocationValue::parse);
        register(BYE,   LocationValue::parse);
    }
}
