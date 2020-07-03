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
import chat.dim.tlv.Tag;

public class LocationValue extends CommandValue {

    private SourceAddressValue sourceAddress = null;
    private MappedAddressValue mappedAddress = null;
    private RelayedAddressValue relayedAddress = null;

    private StringValue nat = null;

    private TimestampValue timestamp = null; // time for signature (in seconds)
    private BinaryValue signature = null;

    public LocationValue(Data data) {
        super(data);
    }

    public LocationValue(List<Field> fields) {
        super(fields);
    }

    public SourceAddressValue getSourceAddress() {
        return sourceAddress;
    }
    public MappedAddressValue getMappedAddress() {
        return mappedAddress;
    }
    public RelayedAddressValue getRelayedAddress() {
        return relayedAddress;
    }

    public StringValue getNat() {
        return nat;
    }

    public TimestampValue getTimestamp() {
        return timestamp;
    }
    public BinaryValue getSignature() {
        return signature;
    }

    @Override
    protected void setField(Field field) {
        Tag type = field.tag;
        if (type.equals(FieldName.SOURCE_ADDRESS))
        {
            assert field.value instanceof SourceAddressValue : "source address error: " + field.value;
            sourceAddress = (SourceAddressValue) field.value;
        }
        else if (type.equals(FieldName.MAPPED_ADDRESS))
        {
            assert field.value instanceof MappedAddressValue : "mapped address error: " + field.value;
            mappedAddress = (MappedAddressValue) field.value;
        }
        else if (type.equals(FieldName.RELAYED_ADDRESS))
        {
            assert field.value instanceof RelayedAddressValue : "relayed address error: " + field.value;
            relayedAddress = (RelayedAddressValue) field.value;
        }
        else if (type.equals(FieldName.TIME))
        {
            assert field.value instanceof TimestampValue : "timestamp error: " + field.value;
            timestamp = (TimestampValue) field.value;
        }
        else if (type.equals(FieldName.SIGNATURE))
        {
            assert field.value instanceof BinaryValue : "signature error: " + field.value;
            signature = (BinaryValue) field.value;
        }
        else if (type.equals(FieldName.NAT))
        {
            assert field.value instanceof StringValue : "NAT error: " + field.value;
            nat = (StringValue) field.value;
        }
        else
        {
            super.setField(field);
        }
    }

    public static LocationValue parse(Data data, FieldName type, FieldLength length) {
        // parse fields
        List<Field> fields = Field.parseFields(data);
        LocationValue value = new LocationValue(data);
        value.setFields(fields);
        return value;
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
        LocationValue value = new LocationValue(fields);
        value.setFields(fields);
        return value;
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
