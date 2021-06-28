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

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.List;

import chat.dim.stun.valus.MappedAddressValue;
import chat.dim.stun.valus.SourceAddressValue;
import chat.dim.tlv.Field;
import chat.dim.tlv.RawValue;
import chat.dim.tlv.StringTag;
import chat.dim.tlv.StringValue;
import chat.dim.tlv.Value32;
import chat.dim.turn.values.RelayedAddressValue;
import chat.dim.type.ByteArray;

public class LocationValue extends CommandValue {

    private SocketAddress sourceAddress = null;
    private SocketAddress mappedAddress = null;
    private SocketAddress relayedAddress = null;

    private long timestamp = 0; // time for signature (in seconds)
    private ByteArray signature = null;

    private String nat = null;

    public LocationValue(ByteArray data, List<Field> fields) {
        super(data, fields);
    }

    public LocationValue(List<Field> fields) {
        super(fields);
    }

    private SocketAddress getAddressValue(StringTag tag) {
        MappedAddressValue value = (MappedAddressValue) get(tag);
        if (value == null) {
            return null;
        }
        return new InetSocketAddress(value.ip, value.port);
    }

    public SocketAddress getSourceAddress() {
        if (sourceAddress == null) {
            sourceAddress = getAddressValue(Command.SOURCE_ADDRESS);
        }
        return sourceAddress;
    }
    public SocketAddress getMappedAddress() {
        if (mappedAddress == null) {
            mappedAddress = getAddressValue(Command.MAPPED_ADDRESS);
        }
        return mappedAddress;
    }
    public SocketAddress getRelayedAddress() {
        if (relayedAddress == null) {
            relayedAddress = getAddressValue(Command.RELAYED_ADDRESS);
        }
        return relayedAddress;
    }

    /**
     *  Get signature time of location info
     *
     * @return timestamp in seconds
     */
    public long getTimestamp() {
        if (timestamp == 0) {
            chat.dim.tlv.Entry.Value value = get(Command.TIME);
            if (value instanceof Value32) {
                timestamp = ((Value32) value).value;
            }
        }
        return timestamp;
    }
    public ByteArray getSignature() {
        if (signature == null) {
            signature = get(Command.SIGNATURE);
        }
        return signature;
    }

    public String getNat() {
        if (nat == null) {
            chat.dim.tlv.Entry.Value value = get(Command.NAT);
            if (value instanceof StringValue) {
                nat = ((StringValue) value).string;
            }
        }
        return nat;
    }

    //
    //  Factories
    //

    public static LocationValue from(LocationValue value) {
        return value;
    }

    public static LocationValue from(ByteArray data) {
        List<Field> fields = Field.parseFields(data);
        return new LocationValue(data, fields);
    }

    // parse value with tag & length
    public static chat.dim.tlv.Entry.Value parse(ByteArray data,
                                                 chat.dim.tlv.Entry.Tag tag, chat.dim.tlv.Entry.Length length) {
        return from(data);
    }

    public static LocationValue create(StringValue identifier,
                                       SourceAddressValue sourceAddress,
                                       MappedAddressValue mappedAddress,
                                       RelayedAddressValue relayedAddress,
                                       Value32 timestamp,
                                       RawValue signature,
                                       StringValue nat) {
        List<Field> fields = new ArrayList<>();
        // ID
        fields.add(Field.create(Command.ID, identifier));
        // SOURCE-ADDRESS
        if (sourceAddress != null) {
            fields.add(Field.create(Command.SOURCE_ADDRESS, sourceAddress));
        }
        // MAPPED-ADDRESS
        if (mappedAddress != null) {
            fields.add(Field.create(Command.MAPPED_ADDRESS, mappedAddress));
        }
        // RELAYED-ADDRESS
        if (relayedAddress != null) {
            fields.add(Field.create(Command.RELAYED_ADDRESS, relayedAddress));
        }
        // TIME
        if (timestamp != null) {
            fields.add(Field.create(Command.TIME, timestamp));
        }
        // SIGNATURE
        if (signature != null) {
            fields.add(Field.create(Command.SIGNATURE, signature));
        }
        // NAT
        if (nat != null) {
            fields.add(Field.create(Command.NAT, nat));
        }
        return new LocationValue(fields);
    }

    public static LocationValue create(String identifier,
                                       SocketAddress sourceAddress,
                                       SocketAddress mappedAddress,
                                       SocketAddress relayedAddress,
                                       long timestamp,
                                       ByteArray signature,
                                       String nat) {
        StringValue identifierValue = StringValue.from(identifier);
        SourceAddressValue sourceAddressValue = null;
        MappedAddressValue mappedAddressValue = null;
        RelayedAddressValue relayedAddressValue = null;
        Value32 timestampValue = null;
        RawValue signatureValue = null;
        StringValue natValue = null;

        InetSocketAddress address;
        // SOURCE-ADDRESS
        if (sourceAddress instanceof InetSocketAddress) {
            address = (InetSocketAddress) sourceAddress;
            sourceAddressValue = SourceAddressValue.create(address.getHostString(), address.getPort());
        }
        // MAPPED-ADDRESS
        if (mappedAddress instanceof InetSocketAddress) {
            address = (InetSocketAddress) mappedAddress;
            mappedAddressValue = MappedAddressValue.create(address.getHostString(), address.getPort());
        }
        // RELAYED-ADDRESS
        if (relayedAddress instanceof InetSocketAddress) {
            address = (InetSocketAddress) relayedAddress;
            relayedAddressValue = RelayedAddressValue.create(address.getHostString(), address.getPort());
        }
        // TIME
        if (timestamp > 0) {
            timestampValue = Value32.from(timestamp);
        }
        // SIGNATURE
        if (signature != null) {
            signatureValue = RawValue.from(signature);
        }
        // NAT
        if (nat != null) {
            natValue = StringValue.from(nat);
        }
        return create(identifierValue, sourceAddressValue, mappedAddressValue, relayedAddressValue,
                timestampValue, signatureValue, natValue);
    }

    public static LocationValue create(StringValue identifier,
                                       SourceAddressValue sourceAddress,
                                       MappedAddressValue mappedAddress,
                                       RelayedAddressValue relayedAddress) {
        return create(identifier, sourceAddress, mappedAddress, relayedAddress,
                null, null, null);
    }

    public static LocationValue create(String identifier,
                                       SocketAddress sourceAddress,
                                       SocketAddress mappedAddress,
                                       SocketAddress relayedAddress) {
        return create(identifier, sourceAddress, mappedAddress, relayedAddress,
                0, null, null);
    }

    public static LocationValue create(StringValue identifier) {
        return create(identifier, null, null, null,
                null, null, null);
    }

    public static LocationValue create(String identifier) {
        return create(identifier, null, null, null,
                0, null, null);
    }
}
