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

import chat.dim.tlv.RawValue;
import chat.dim.tlv.Triad;
import chat.dim.type.ByteArray;

public class AttributeValue extends RawValue {

    public AttributeValue(ByteArray data) {
        super(data);
    }

    //
    //  Factory
    //

    public static AttributeValue parse(ByteArray data, AttributeType type, AttributeLength length) {
        Class clazz = attributeValueClasses.get(type);
        if (clazz != null) {
            // create instance by subclass
            return create(clazz, data, type, length);
        }
        return new AttributeValue(data);
    }

    //-------- Runtime --------

    private static final Map<Triad.Tag, Class> attributeValueClasses = new HashMap<>();

    public static void register(Triad.Tag type, Class clazz) {
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
    private static AttributeValue create(Class clazz, ByteArray data, AttributeType type, AttributeLength length) {
        // try 'Clazz.parse(data, type, length)'
        try {
            Method method = clazz.getMethod("parse", ByteArray.class, AttributeType.class, AttributeLength.class);
            if (method.getDeclaringClass().equals(clazz)) {
                // only invoke the method 'parse()' declared in this class
                return (AttributeValue) method.invoke(null, data, type, length);
            }
        } catch (NoSuchMethodException | IllegalAccessException | InvocationTargetException e) {
            //e.printStackTrace();
        }
        return null;
    }
}
