/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
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
package chat.dim.tlv;

import java.util.HashMap;
import java.util.Map;

import chat.dim.type.ByteArray;

public abstract class FieldParser<F extends Field> extends Parser<F, StringTag, VarLength, Triad.Value>
        implements Field.TagParser, Field.LengthParser, Field.ValueParser {

    @Override
    protected Field.TagParser getTagParser() {
        return this;
    }
    @Override
    protected Field.LengthParser getLengthParser() {
        return this;
    }
    @Override
    protected Field.ValueParser getValueParser() {
        return this;
    }

    @Override
    public StringTag parseTag(ByteArray data) {
        return StringTag.from(data);
    }

    @Override
    public VarLength parseLength(ByteArray data, StringTag type) {
        return VarLength.from(data);
    }

    @Override
    public Triad.Value parseValue(ByteArray data, StringTag type, VarLength length) {
        Field.ValueParser parser = valueParsers.get(type.string);
        if (parser == null) {
            return RawValue.from(data);
        } else {
            return parser.parseValue(data, type, length);
        }
    }

    //-------- Runtime --------

    private static final Map<String, Field.ValueParser> valueParsers = new HashMap<>();

    public static void register(String type, Field.ValueParser parser) {
        if (parser == null) {
            valueParsers.remove(type);
        } else {
            valueParsers.put(type, parser);
        }
    }
}
