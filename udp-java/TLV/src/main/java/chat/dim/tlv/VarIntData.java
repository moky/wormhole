/* license: https://mit-license.org
 *
 *  TLV: Tag Length Value
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
package chat.dim.tlv;

/**
 *  Variable Integer
 */
public class VarIntData extends IntegerData {

    public VarIntData(Data data, long value) {
        super(data, value);
    }

    public VarIntData(long value) {
        super(parseLong(value), value);
    }

    //
    //  Factories
    //

    public static VarIntData fromBytes(byte[] bytes) {
        return fromData(new Data(bytes));
    }

    public static VarIntData fromData(Data data) {
        Result res = parseBytes(data.buffer, data.offset, data.offset + data.length);
        if (res.length < data.getLength()) {
            data = data.slice(0, res.length);
        }
        return new VarIntData(data, res.value);
    }

    private static Data parseLong(long value) {
        byte[] buffer = new byte[8];
        int index = 0;
        for (; value > 0x7F /*&& index < 8*/; ++index) {
            buffer[index] = (byte) ((value & 0x7F) | 0x80);
            value >>= 7;
        }
        buffer[index] = (byte) (value & 0x7F);
        return new Data(buffer, 0, index + 1);
    }

    private static Result parseBytes(byte[] bytes, int start, int end) {
        long value = 0;
        int offset = 0;
        int index = start;
        byte ch = (byte) 0x80;
        for (; index < end && (ch & 0x80) != 0; ++index) {
            ch = bytes[index];
            value |= (ch & 0x7F) << offset;
            offset += 7;
        }
        return new Result(value, index - start);
    }

    private static final class Result {

        final long value;
        final int length;

        Result(long value, int length) {
            super();
            this.value = value;
            this.length = length;
        }
    }
}
