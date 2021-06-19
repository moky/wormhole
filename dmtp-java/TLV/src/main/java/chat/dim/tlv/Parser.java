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

import chat.dim.type.ByteArray;

import java.util.ArrayList;
import java.util.List;

/*
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |         Type                  |            Length             |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |                         Value (variable)                ....
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 */

public class Parser implements Triad.Parser {

    @Override
    public Triad.Tag parseTag(ByteArray data) {
        if (data.getLength() < 2) {
            // error
            return null;
        }
        return new Tag16(data.slice(0, 2));
    }

    @Override
    public Triad.Length parseLength(ByteArray data, Triad.Tag type) {
        if (data.getLength() < 2) {
            // error
            return null;
        }
        return new Length16(data.slice(0, 2));
    }

    @Override
    public Triad.Value parseValue(ByteArray data, Triad.Tag type, Triad.Length length) {
        int size;
        if (length == null) {
            size = data.getLength();
        } else {
            size = length.getIntValue();
            if (size > data.getLength()) {
                // error
                return null;
            }
        }
        return new RawValue(data.slice(0, size));
    }

    @Override
    public Triad parseTriad(ByteArray data) {
        // get tag field
        Triad.Tag type = parseTag(data);
        if (type == null) {
            return null;
        }
        int offset = type.getLength();
        // get length field
        Triad.Length length = parseLength(data.slice(offset), type);
        if (length != null) {
            offset += length.getLength();
        }
        // get value field
        Triad.Value value = parseValue(data.slice(offset), type, length);
        if (value != null) {
            offset += value.getLength();
        }
        return new TagLengthValue(data.slice(0, offset), type, length, value);
    }

    @Override
    public List<Triad> parse(ByteArray data) {
        List<Triad> array = new ArrayList<>();
        Triad item;
        while (data.getLength() > 0) {
            item = parseTriad(data);
            if (item == null) {
                // data error
                break;
            }
            array.add(item);
            // next item
            assert item.getLength() > 0 : "Triad error";
            data.slice(item.getLength());
        }
        return array;
    }
}
