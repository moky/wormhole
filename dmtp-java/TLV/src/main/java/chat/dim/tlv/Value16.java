/* license: https://mit-license.org
 *
 *  TLV: Tag Length Value
 *
 *                                Written in 2021 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Albert Moky
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
package chat.dim.tlv;

import chat.dim.network.DataConvert;
import chat.dim.type.ByteArray;
import chat.dim.type.UInt16Data;

/**
 *  Integer Value (16 bits)
 *  ~~~~~~~~~~~~~~~~~~~~~~~
 *
 *  Network Byte Order
 */
public class Value16 extends UInt16Data implements Entry.Value {

    public static final Value16 ZERO = from(UInt16Data.ZERO);

    public Value16(UInt16Data data) {
        super(data, data.value, data.endian);
    }

    public Value16(ByteArray data, int value, Endian endian) {
        super(data, value, endian);
    }

    //
    //  Factories
    //

    public static Value16 from(Value16 tag) {
        return tag;
    }

    public static Value16 from(UInt16Data data) {
        return new Value16(data, data.value, data.endian);
    }

    public static Value16 from(ByteArray data) {
        if (data.getSize() < 2) {
            return null;
        } else if (data.getSize() > 2) {
            data = data.slice(0, 2);
        }
        return new Value16(DataConvert.getUInt16Data(data));
    }

    public static Value16 from(int value) {
        return new Value16(DataConvert.getUInt16Data(value));
    }

    // parse value with tag & length
    public static Entry.Value parse(ByteArray data, Entry.Tag tag, Entry.Length length) {
        return from(data);
    }
}
