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

/*
 *       0                   1                   2                   3
 *       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |         Type                  |            Length             |
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 *      |                         Value (variable)                ....
 *      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 */

import java.util.ArrayList;
import java.util.List;

public class TagLengthValue extends Data {

    public final Tag tag;
    public final Value value;

    public TagLengthValue(byte[] data, Tag type, Value value) {
        super(data);
        this.tag = type;
        this.value = value;
    }

    //
    //  Parsers
    //

    public static List<TagLengthValue> parseAll(byte[] data) {
        List<TagLengthValue> array = new ArrayList<>();
        TagLengthValue item;
        int remaining = data.length;
        int pos;
        while (remaining > 0) {
            item = parse(data);
            if (item == null) {
                // data error
                break;
            }
            array.add(item);
            // next item
            pos = item.data.length;
            data = slice(data, pos);
            remaining -= pos;
        }
        return array;
    }

    public static TagLengthValue parse(byte[] data) {
        // get type
        Tag type = parseTag(data);
        if (type == null) {
            return null;
        }
        int offset = type.data.length;
        // get length
        Length length = parseLength(slice(data, offset), type);
        if (length != null) {
            offset += length.data.length;
        }
        // get value
        Value value = parseValue(slice(data, offset), type, length);
        if (value != null) {
            offset += value.data.length;
        }
        // create
        if (offset < data.length) {
            return new TagLengthValue(slice(data, 0, offset), type, value);
        } else {
            assert offset == data.length : "offset error: " + offset + " > " + data.length;
            return new TagLengthValue(data, type, value);
        }
    }

    public static Tag parseTag(byte[] data) {
        return Tag.parse(data);
    }

    public static Length parseLength(byte[] data, Tag type) {
        return Length.parse(data, type);
    }

    public static Value parseValue(byte[] data, Tag type, Length length) {
        return Value.parse(data, type, length);
    }
}
