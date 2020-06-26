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

    public VarIntData(byte[] data, long value) {
        super(data, value);
    }

    public static VarIntData fromBytes(byte[] data) {
        int length = data.length;
        if (length < 1) {
            return null;
        }
        Result res = parseBytes(data);
        if (res.length < length) {
            data = slice(data, 0, res.length);
        }
        return new VarIntData(data, res.value);
    }

    public static VarIntData fromLong(long value) {
        byte[] data = intToBytes(value);
        return new VarIntData(data, value);
    }

    //
    //  Converting
    //

    private static final class Result {
        final long value;
        final int length;
        Result(long value, int length) {
            this.value = value;
            this.length = length;
        }
    }

    private static Result parseBytes(byte[] data) {
        long value = 0;
        int index = 0;
        int offset = 0;
        byte ch;
        do {
            ch = data[index];
            value |= (ch & 0x7F) << offset;
            index += 1;
            offset += 7;
        } while ((ch & 0x80) != 0);
        return new Result(value, index);
    }

    public static long bytesToLong(byte[] data) {
        return parseBytes(data).value;
    }

    public static byte[] intToBytes(long value) {
        byte[] buffer = new byte[8];
        int index = 0;
        while (value > 0x7F) {
            buffer[index] = (byte) ((value & 0x7F) | 0x80);
            value >>= 7;
            index += 1;
        }
        buffer[index] = (byte) (value & 0x7F);
        return slice(buffer, 0, index + 1);
    }
}
