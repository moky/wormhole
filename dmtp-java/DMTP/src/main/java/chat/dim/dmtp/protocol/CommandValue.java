/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
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
package chat.dim.dmtp.protocol;

import java.util.ArrayList;
import java.util.List;

import chat.dim.tlv.Field;
import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;
import chat.dim.tlv.Value;
import chat.dim.tlv.values.MapValue;
import chat.dim.tlv.values.StringValue;
import chat.dim.type.ByteArray;

public class CommandValue extends MapValue<Field> {

    private String identifier = null;

    public CommandValue(ByteArray data, List<Field> fields) {
        super(data, fields);
    }

    public CommandValue(List<Field> fields) {
        super(fields);
    }

    public String getIdentifier() {
        if (identifier == null) {
            identifier = getStringValue(Command.ID);
        }
        return identifier;
    }

    //
    //  Factories
    //

    public static CommandValue from(CommandValue value) {
        return value;
    }

    public static CommandValue from(ByteArray data) {
        List<Field> fields = Field.parseFields(data);
        return new CommandValue(data, fields);
    }

    public static CommandValue create(String identifier) {
        Field id = Field.create(Command.ID, StringValue.from(identifier));
        List<Field> fields = new ArrayList<>();
        fields.add(id);
        return new CommandValue(fields);
    }

    // parse value with tag & length
    public static Value parse(ByteArray data, Tag tag, Length length) {
        return from(data);
    }
}
