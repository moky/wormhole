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
package chat.dim.dmtp.values;

import java.nio.charset.Charset;

import chat.dim.dmtp.fields.FieldLength;
import chat.dim.dmtp.fields.FieldName;
import chat.dim.dmtp.fields.FieldValue;
import chat.dim.tlv.Data;

public class StringValue extends FieldValue {

    public final String string;

    public StringValue(Data data) {
        super(data);
        this.string = new String(data.getBytes(), Charset.forName("UTF-8"));
    }

    public StringValue(Data data, String string) {
        super(data);
        this.string = string;
    }

    public StringValue(String string) {
        super(string.getBytes(Charset.forName("UTF-8")));
        this.string = string;
    }

    @Override
    public String toString() {
        return string;
    }

    public static StringValue parse(Data data, FieldName type, FieldLength length) {
        String string = data.toString();
        return new StringValue(data, string);
    }
}
