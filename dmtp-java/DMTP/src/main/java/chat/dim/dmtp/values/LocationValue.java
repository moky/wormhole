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
package chat.dim.dmtp.values;

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.List;

import chat.dim.dmtp.fields.Field;
import chat.dim.dmtp.fields.FieldLength;
import chat.dim.dmtp.fields.FieldName;
import chat.dim.tlv.Data;

public class LocationValue extends CommandValue {

    private SocketAddress sourceAddress = null;
    private SocketAddress mappedAddress = null;
    private SocketAddress relayedAddress = null;

    private long timestamp = 0; // time for signature (in seconds)
    private Data signature = null;

    private String nat = null;

    public LocationValue(Data data, List<Field> fields) {
        super(data, fields);
    }

    public LocationValue(List<Field> fields) {
        super(fields);
    }

    protected SocketAddress getAddress(FieldName tag) {
        MappedAddressValue value = (MappedAddressValue) get(tag.name);
        if (value == null) {
            return null;
        }
        return new InetSocketAddress(value.ip, value.port);
    }

    public SocketAddress getSourceAddress() {
        if (sourceAddress == null) {
            sourceAddress = getAddress(FieldName.SOURCE_ADDRESS);
        }
        return sourceAddress;
    }
    public SocketAddress getMappedAddress() {
        if (mappedAddress == null) {
            mappedAddress = getAddress(FieldName.MAPPED_ADDRESS);
        }
        return mappedAddress;
    }
    public SocketAddress getRelayedAddress() {
        if (relayedAddress == null) {
            relayedAddress = getAddress(FieldName.RELAYED_ADDRESS);
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
            TimestampValue value = (TimestampValue) get(FieldName.TIME);
            if (value != null) {
                timestamp = value.value;
            }
        }
        return timestamp;
    }
    public Data getSignature() {
        if (signature == null) {
            signature = (BinaryValue) get(FieldName.SIGNATURE);
        }
        return signature;
    }

    public String getNat() {
        if (nat == null) {
            StringValue value = (StringValue) get(FieldName.NAT);
            if (value != null) {
                nat = value.string;
            }
        }
        return nat;
    }

    @SuppressWarnings("unused")
    public static LocationValue parse(Data data, FieldName type, FieldLength length) {
        // parse fields
        List<Field> fields = Field.parseFields(data);
        return new LocationValue(data, fields);
    }


    //
    //  Factories
    //

    public static LocationValue create(StringValue identifier,
                                       SourceAddressValue sourceAddress,
                                       MappedAddressValue mappedAddress,
                                       RelayedAddressValue relayedAddress,
                                       TimestampValue timestamp,
                                       BinaryValue signature,
                                       StringValue nat) {
        List<Field> fields = new ArrayList<>();
        // ID
        fields.add(new Field(FieldName.ID, identifier));
        // SOURCE-ADDRESS
        if (sourceAddress != null) {
            fields.add(new Field(FieldName.SOURCE_ADDRESS, sourceAddress));
        }
        // MAPPED-ADDRESS
        if (mappedAddress != null) {
            fields.add(new Field(FieldName.MAPPED_ADDRESS, mappedAddress));
        }
        // RELAYED-ADDRESS
        if (relayedAddress != null) {
            fields.add(new Field(FieldName.RELAYED_ADDRESS, relayedAddress));
        }
        // TIME
        if (timestamp != null) {
            fields.add(new Field(FieldName.TIME, timestamp));
        }
        // SIGNATURE
        if (signature != null) {
            fields.add(new Field(FieldName.SIGNATURE, signature));
        }
        // NAT
        if (nat != null) {
            fields.add(new Field(FieldName.NAT, nat));
        }
        return new LocationValue(fields);
    }

    public static LocationValue create(String identifier,
                                       SocketAddress sourceAddress,
                                       SocketAddress mappedAddress,
                                       SocketAddress relayedAddress,
                                       long timestamp,
                                       Data signature,
                                       String nat) {
        StringValue identifierValue = new StringValue(identifier);
        SourceAddressValue sourceAddressValue = null;
        MappedAddressValue mappedAddressValue = null;
        RelayedAddressValue relayedAddressValue = null;
        TimestampValue timestampValue = null;
        BinaryValue signatureValue = null;
        StringValue natValue = null;

        InetSocketAddress address;
        // SOURCE-ADDRESS
        if (sourceAddress instanceof InetSocketAddress) {
            address = (InetSocketAddress) sourceAddress;
            sourceAddressValue = new SourceAddressValue(address.getHostString(), address.getPort());
        }
        // MAPPED-ADDRESS
        if (mappedAddress instanceof InetSocketAddress) {
            address = (InetSocketAddress) mappedAddress;
            mappedAddressValue = new MappedAddressValue(address.getHostString(), address.getPort());
        }
        // RELAYED-ADDRESS
        if (relayedAddress instanceof InetSocketAddress) {
            address = (InetSocketAddress) relayedAddress;
            relayedAddressValue = new RelayedAddressValue(address.getHostString(), address.getPort());
        }
        // TIME
        if (timestamp > 0) {
            timestampValue = new TimestampValue(timestamp);
        }
        // SIGNATURE
        if (signature != null) {
            signatureValue = new BinaryValue(signature);
        }
        // NAT
        if (nat != null) {
            natValue = new StringValue(nat);
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
