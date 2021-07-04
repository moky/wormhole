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

public abstract class Parser<E extends Entry<T, L, V>, T extends Tag, L extends Length, V extends Value>
        implements Entry.Parser<E, T, L, V> {

    // get TLV parsers
    protected abstract Tag.Parser<T> getTagParser();
    protected abstract Length.Parser<T, L> getLengthParser();
    protected abstract Value.Parser<T, L, V> getValueParser();

    // create TLV triad
    protected abstract E createEntry(ByteArray data, T type, L length, V value);

    @Override
    public E parseEntry(ByteArray data) {
        // 1. get tag field
        T type = getTagParser().parseTag(data);
        if (type == null) {
            return null;
        }
        int offset = type.getSize();
        int valueLength;
        // 2. get length field
        L length = getLengthParser().parseLength(data.slice(offset), type);
        if (length == null) {
            // if length not defined, use the rest data as value
            valueLength = data.getSize() - offset;
        } else {
            valueLength = length.getIntValue();
            offset += length.getSize();
        }
        // 3. get value field
        V value = getValueParser().parseValue(data.slice(offset, offset + valueLength), type, length);
        if (value != null) {
            offset += value.getSize();
        }
        return createEntry(data.slice(0, offset), type, length, value);
    }

    @Override
    public List<E> parseEntries(ByteArray data) {
        List<E> array = new ArrayList<>();
        E item;
        while (data.getSize() > 0) {
            item = parseEntry(data);
            if (item == null) {
                // data error
                break;
            }
            array.add(item);
            // next item
            assert item.getSize() > 0 : "TLV triads error";
            data = data.slice(item.getSize());
        }
        return array;
    }
}
