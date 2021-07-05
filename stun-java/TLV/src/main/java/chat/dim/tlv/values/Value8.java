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
package chat.dim.tlv.values;

import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;
import chat.dim.tlv.Value;
import chat.dim.type.ByteArray;
import chat.dim.type.UInt8Data;

/**
 *  Fixed Char Value (8 bits)
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public class Value8 extends UInt8Data implements Value {

    public static final Value8 ZERO = from(UInt8Data.ZERO);

    public Value8(ByteArray data) {
        super(data);
    }

    public Value8(byte value) {
        super(value);
    }

    public Value8(int value) {
        super(value);
    }

    //
    //  Factories
    //

    public static Value8 from(Value8 value) {
        return value;
    }

    public static Value8 from(UInt8Data data) {
        return new Value8(data);
    }

    public static Value8 from(ByteArray data) {
        if (data.getSize() < 1) {
            return null;
        } else if (data.getSize() > 1) {
            data = data.slice(0, 1);
        }
        return new Value8(data);
    }

    public static Value8 from(byte value) {
        return new Value8(value);
    }
    public static Value8 from(int value) {
        return new Value8(value);
    }

    // parse value with tag & length
    public static Value parse(ByteArray data, Tag tag, Length length) {
        return from(data);
    }
}
