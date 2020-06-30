/* license: https://mit-license.org
 *
 *  STUN: Session Traversal Utilities for NAT
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
package chat.dim.stun.attributes;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;

import chat.dim.stun.valus.*;
import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;
import chat.dim.tlv.Value;

public class AttributeValue extends Value {

    public AttributeValue(byte[] data) {
        super(data);
    }

    public static AttributeValue parse(byte[] data, Tag type, Length length) {
        Class clazz = attributeValueClasses.get(type);
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
        return new AttributeValue(data);
    }

    //-------- Runtime --------

    private static Map<Tag, Class> attributeValueClasses = new HashMap<>();

    public static void register(Tag type, Class clazz) {
        if (clazz == null) {
            attributeValueClasses.remove(type);
        } else if (clazz.equals(AttributeValue.class)) {
            throw new IllegalArgumentException("should not add AttributeValue itself!");
        } else {
            assert AttributeValue.class.isAssignableFrom(clazz) : "error: " + clazz;
            attributeValueClasses.put(type, clazz);
        }
    }

    @SuppressWarnings("unchecked")
    private static AttributeValue create(Class clazz, byte[] data, Tag type, Length length) {
        // try 'Clazz.parse(data, type, length)'
        try {
            Method method = clazz.getMethod("parse", byte[].class, Tag.class, Length.class);
            if (method.getDeclaringClass().equals(clazz)) {
                // only invoke the method 'parse()' declared in this class
                return (AttributeValue) method.invoke(null, data, type, length);
            }
        } catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException e) {
            //e.printStackTrace();
        }
        return null;
    }

    static {
        register(AttributeType.MappedAddress, MappedAddressValue.class);
        //register(AttributeType.XorMappedAddress, XorMappedAddressValue.class);
        //register(AttributeType.XorMappedAddress2, XorMappedAddressValue2.class);

        register(AttributeType.ResponseAddress, ResponseAddressValue.class);
        register(AttributeType.ChangeRequest, ChangeRequestValue.class);
        register(AttributeType.SourceAddress, SourceAddressValue.class);
        register(AttributeType.ChangedAddress, ChangedAddressValue.class);

        register(AttributeType.Software, SoftwareValue.class);
    }
}
