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

import chat.dim.dmtp.fields.FieldLength;
import chat.dim.dmtp.fields.FieldName;
import chat.dim.dmtp.fields.FieldValue;

public class ByteValue extends FieldValue {

    public final int value;

    public ByteValue(byte[] data, int value) {
        super(data);
        this.value = value;
    }

    public ByteValue(int value) {
        this(build(value), value);
    }

    private static byte[] build(int value) {
        byte[] data = new byte[1];
        data[0] = (byte) (value & 0xFF);
        return data;
    }

    @Override
    public String toString() {
        return Integer.toString(value & 0xFF);
    }

    public static ByteValue parse(byte[] data, FieldName type, FieldLength length) {
        if (length != null && length.value != 1) {
            //throw new ArrayIndexOutOfBoundsException("length error: " + length);
            return null;
        } else if (data.length < 1) {
            //throw new ArrayIndexOutOfBoundsException("length error: " + length);
            return null;
        }
        return new ByteValue(data[0]);
    }
}
