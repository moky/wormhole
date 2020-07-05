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

    public TagLengthValue(TagLengthValue tlv) {
        super(tlv);
        tag = tlv.tag;
        value = tlv.value;
    }

    public TagLengthValue(Data data, Tag type, Value value) {
        super(data);
        this.tag = type;
        this.value = value;
    }

    public TagLengthValue(byte[] bytes, Tag type, Value value) {
        super(bytes);
        this.tag = type;
        this.value = value;
    }

    public TagLengthValue(Tag type, Length length, Value value) {
        this(build(type, length, value), type, value);
    }

    private static Data build(Tag type, Length length, Value value) {
        Data data = type;
        if (length != null) {
            data = data.concat(length);
        }
        if (value != null) {
            data = data.concat(value);
        }
        return data;
    }

    @Override
    public String toString() {
        return "/* " + getClass().getSimpleName() + " */ " + tag + ": \"" + value + "\"";
    }

    //
    //  Parser
    //

    private static final Parser parser = new Parser();

    public static List<TagLengthValue> parseAll(Data data) {
        //noinspection unchecked
        return (List<TagLengthValue>) parser.parseAll(data);
    }

    protected static class Parser {

        public List parseAll(Data data) {
            List<TagLengthValue> array = new ArrayList<>();
            TagLengthValue item;
            int remaining = data.getLength();
            while (remaining > 0) {
                item = parse(data);
                if (item == null) {
                    // data error
                    break;
                }
                array.add(item);
                // next item
                data = data.slice(item.getLength());
                remaining -= item.getLength();
            }
            return array;
        }

        private TagLengthValue parse(Data data) {
            // get type
            Tag type = parseTag(data);
            if (type == null) {
                return null;
            }
            Value value;
            int offset = type.getLength();
            assert offset <= data.getLength() : "data length error: " + data.getLength() + ", offset: " + offset;
            // get length
            Length length = parseLength(data.slice(offset), type);
            if (length == null) {
                // get value with unlimited length
                value = parseValue(data.slice(offset), type, null);
            } else {
                // get value with limited length
                offset += length.getLength();
                int end = offset + length.getIntValue();
                if (end < offset || end > data.getLength()) {
                    throw new IndexOutOfBoundsException("data length error: " + length.value + ", " + data.getLength());
                }
                value = parseValue(data.slice(offset, end), type, length);
            }
            if (value != null) {
                offset += value.getLength();
            }
            // check length
            if (offset > data.getLength()) {
                throw new AssertionError("TLV length error: " + length + ", " + data.getLength());
            } else if (offset < data.getLength()) {
                data = data.slice(0, offset);
            }
            return create(data, type, value);
        }

        protected Tag parseTag(Data data) {
            // TODO: override for user-defined Tag
            return Tag.parse(data);
        }

        protected Length parseLength(Data data, Tag type) {
            // TODO: override for user-defined Length
            return Length.parse(data, type);
        }

        protected Value parseValue(Data data, Tag type, Length length) {
            // TODO: override for user-defined Value
            return Value.parse(data, type, length);
        }

        protected TagLengthValue create(Data data, Tag type, Value value) {
            // TODO: override for user-defined TLV
            return new TagLengthValue(data, type, value);
        }
    }
}
