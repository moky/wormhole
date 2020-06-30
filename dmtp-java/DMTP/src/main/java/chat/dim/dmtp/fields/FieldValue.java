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
package chat.dim.dmtp.fields;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;

import chat.dim.dmtp.values.MappedAddressValue;
import chat.dim.dmtp.values.RelayedAddressValue;
import chat.dim.dmtp.values.SourceAddressValue;
import chat.dim.dmtp.values.BinaryValue;
import chat.dim.dmtp.values.StringValue;
import chat.dim.dmtp.values.TimestampValue;
import chat.dim.tlv.Value;

public class FieldValue extends Value {

    public FieldValue(byte[] data) {
        super(data);
    }

    public static FieldValue parse(byte[] data, FieldName type, FieldLength length) {
        Class clazz = fieldValueClasses.get(type);
        if (clazz != null) {
            // create instance by subclass
            return create(clazz, data, type, length);
        }
        // check length
        if (length == null || length.value == 0) {
            //throw new ArrayIndexOutOfBoundsException("length error: " + length);
            return null;
        } else {
            int len = length.getIntValue();
            int dataLen = data.length;
            if (len < 0 || len > dataLen) {
                //throw new ArrayIndexOutOfBoundsException("data length error: " + data.length + ", " + length.value);
                return null;
            } else if (len < dataLen) {
                data = slice(data, 0, len);
            }
        }
        return new FieldValue(data);
    }


    //-------- Runtime --------

    private static Map<FieldName, Class> fieldValueClasses = new HashMap<>();

    public static void register(FieldName type, Class clazz) {
        if (clazz == null) {
            fieldValueClasses.remove(type);
        } else if (clazz.equals(FieldValue.class)) {
            throw new IllegalArgumentException("should not add AttributeValue itself!");
        } else {
            assert FieldValue.class.isAssignableFrom(clazz) : "error: " + clazz;
            fieldValueClasses.put(type, clazz);
        }
    }

    @SuppressWarnings("unchecked")
    private static FieldValue create(Class clazz, byte[] data, FieldName type, FieldLength length) {
        // try 'Clazz.parse(data, type, length)'
        try {
            Method method = clazz.getMethod("parse", byte[].class, FieldName.class, FieldLength.class);
            if (method.getDeclaringClass().equals(clazz)) {
                // only invoke the method 'parse()' declared in this class
                return (FieldValue) method.invoke(null, data, type, length);
            }
        } catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException e) {
            //e.printStackTrace();
        }
        return null;
    }

    //
    //  Field names
    //

    public static final FieldName ID = new FieldName("ID");       // user ID
    public static final FieldName SOURCE_ADDRESS = new FieldName("SOURCE-ADDRESS");
    public static final FieldName MAPPED_ADDRESS = new FieldName("MAPPED-ADDRESS");
    public static final FieldName RELAYED_ADDRESS = new FieldName("RELAYED-ADDRESS");
    public static final FieldName TIME = new FieldName("TIME");   // timestamp (uint32) stored in network order (big endian)
    public static final FieldName SIGNATURE = new FieldName("SIGNATURE");
    public static final FieldName NAT = new FieldName("NAT");     // NAT type

    static {
        register(ID, StringValue.class);
        register(SOURCE_ADDRESS, SourceAddressValue.class);
        register(MAPPED_ADDRESS, MappedAddressValue.class);
        register(RELAYED_ADDRESS, RelayedAddressValue.class);
        register(TIME, TimestampValue.class);
        register(SIGNATURE, BinaryValue.class);
        register(NAT, StringValue.class);
    }
}
