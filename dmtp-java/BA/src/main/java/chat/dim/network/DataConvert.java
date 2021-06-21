/* license: https://mit-license.org
 *
 *  BA: Byte Array
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
package chat.dim.network;

import chat.dim.type.ByteArray;
import chat.dim.type.IntegerData;
import chat.dim.type.UInt16Data;
import chat.dim.type.UInt32Data;

/**
 *  Network Byte Order Converter
 *  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 */
public interface DataConvert extends IntegerData {

    //
    //  data => int16
    //
    static int getInt16Value(ByteArray data) {
        return (int) IntegerData.getValue(data, 0, 2, Endian.BIG_ENDIAN);
    }
    static int getUInt16Value(ByteArray data) {
        return (int) IntegerData.getValue(data, 0, 2, Endian.BIG_ENDIAN);
    }
    static int getInt16Value(ByteArray data, int start) {
        return (int) IntegerData.getValue(data, start, 2, Endian.BIG_ENDIAN);
    }
    static int getUInt16Value(ByteArray data, int start) {
        return (int) IntegerData.getValue(data, start, 2, Endian.BIG_ENDIAN);
    }

    //
    //  data => int32
    //
    static int getInt32Value(ByteArray data) {
        return (int) IntegerData.getValue(data, 0, 4, Endian.BIG_ENDIAN);
    }
    static long getUInt32Value(ByteArray data) {
        return IntegerData.getValue(data, 0, 4, Endian.BIG_ENDIAN);
    }
    static int getInt32Value(ByteArray data, int start) {
        return (int) IntegerData.getValue(data, start, 4, Endian.BIG_ENDIAN);
    }
    static long getUInt32Value(ByteArray data, int start) {
        return IntegerData.getValue(data, start, 4, Endian.BIG_ENDIAN);
    }

    //
    //  int16 data
    //
    static UInt16Data getUInt16Data(int value) {
        return UInt16Data.from(value, Endian.BIG_ENDIAN);
    }
    static UInt16Data getUInt16Data(ByteArray data) {
        return UInt16Data.from(data, Endian.BIG_ENDIAN);
    }
    static UInt16Data getUInt16Data(ByteArray data, int start) {
        return UInt16Data.from(data.slice(start), Endian.BIG_ENDIAN);
    }

    //
    //  int32 data
    //
    static UInt32Data getUInt32Data(long value) {
        return UInt32Data.from(value, Endian.BIG_ENDIAN);
    }
    static UInt32Data getUInt32Data(ByteArray data) {
        return UInt32Data.from(data, Endian.BIG_ENDIAN);
    }
    static UInt32Data getUInt32Data(ByteArray data, int start) {
        return UInt32Data.from(data.slice(start), Endian.BIG_ENDIAN);
    }
}
