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

    public TagLengthValue(Tag type, Length length, Value value) {
        this(build(type, length, value), type, value);
    }

    private static byte[] build(Tag type, Length length, Value value) {
        byte[] data = type.data;
        if (length != null) {
            data = concat(data, length.data);
        }
        if (value != null) {
            data = concat(data, value.data);
        }
        return data;
    }

    //
    //  Parser
    //

    private static final Parser parser = new Parser();

    public static List<TagLengthValue> parseAll(byte[] data) {
        //noinspection unchecked
        return (List<TagLengthValue>) parser.parseAll(data);
    }

    protected static class Parser {

        public List parseAll(byte[] data) {
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
                pos = item.length;
                data = slice(data, pos);
                remaining -= pos;
            }
            return array;
        }

        private TagLengthValue parse(byte[] data) {
            // get type
            Tag type = parseTag(data);
            if (type == null) {
                return null;
            }
            Value value = null;
            int dataLen = data.length;
            int offset = type.length;
            if (0 < offset && offset < dataLen) {
                // get length
                Length length = parseLength(slice(data, offset), type);
                // get value
                if (length == null) {
                    value = parseValue(slice(data, offset), type, null);
                } else {
                    offset += length.length;
                    int end = offset + (int) length.value;
                    if (offset < end && end <= dataLen) {
                        value = parseValue(slice(data, offset, end), type, length);
                    }
                }
                if (value != null) {
                    offset += value.length;
                }
            }
            // check length
            if (offset <= 0 || offset > dataLen) {
                throw new AssertionError("TLV length error: " + offset + ", " + dataLen);
            } else if (offset < dataLen) {
                data = slice(data, 0, offset);
            }
            return create(data, type, value);
        }

        protected TagLengthValue create(byte[] data, Tag type, Value value) {
            return new TagLengthValue(data, type, value);
        }

        protected Tag parseTag(byte[] data) {
            return Tag.parse(data);
        }

        protected Length parseLength(byte[] data, Tag type) {
            return Length.parse(data, type);
        }

        protected Value parseValue(byte[] data, Tag type, Length length) {
            return Value.parse(data, type, length);
        }
    }
}
