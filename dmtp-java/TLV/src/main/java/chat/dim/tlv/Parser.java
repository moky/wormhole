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

import java.util.ArrayList;
import java.util.List;

import chat.dim.type.ByteArray;

/*
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |         Type                  |            Length             |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |                         Value (variable)                ....
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 */

public abstract class Parser<A extends Triad<T,L,V>, T extends Triad.Tag, L extends Triad.Length, V extends Triad.Value>
        implements Triad.Parser<A, T, L, V> {

    @Override
    public A parseTriad(ByteArray data) {
        // get tag field
        T type = parseTag(data);
        if (type == null) {
            return null;
        }
        int offset = type.getSize();
        int valueLength;
        // get length field
        L length = parseLength(data.slice(offset), type);
        if (length == null) {
            // if length not defined, use the rest data as value
            valueLength = data.getSize() - offset;
        } else {
            valueLength = length.getIntValue();
            offset += length.getSize();
        }
        // get value field
        V value = parseValue(data.slice(offset, offset + valueLength), type, length);
        if (value != null) {
            offset += value.getSize();
        }
        return createTriad(data.slice(0, offset), type, length, value);
    }
    protected abstract A createTriad(ByteArray data, T type, L length, V value);

    @Override
    public List<A> parseAll(ByteArray data) {
        List<A> array = new ArrayList<>();
        A item;
        while (data.getSize() > 0) {
            item = parseTriad(data);
            if (item == null) {
                // data error
                break;
            }
            array.add(item);
            // next item
            assert item.getSize() > 0 : "Triad error";
            data = data.slice(item.getSize());
        }
        return array;
    }
}
