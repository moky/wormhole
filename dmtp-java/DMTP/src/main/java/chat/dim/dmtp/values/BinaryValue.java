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

import java.util.Arrays;

import chat.dim.dmtp.fields.FieldLength;
import chat.dim.dmtp.fields.FieldName;
import chat.dim.dmtp.fields.FieldValue;

public class BinaryValue extends FieldValue {

    public BinaryValue(byte[] data) {
        super(data);
    }

    @Override
    public String toString() {
        return Arrays.toString(data);
    }

    public static BinaryValue parse(byte[] data, FieldName type, FieldLength length) {
        // check length
        if (length == null || length.value == 0) {
            //throw new ArrayIndexOutOfBoundsException("length error: " + length);
            return null;
        } else {
            int len = length.getIntValue();
            int dataLen = data.length;
            if (len < 0 || len > dataLen) {
                //throw new ArrayIndexOutOfBoundsException("data length error: " + data.length + ", " + length.value);
                return null;
            } else if (len < dataLen) {
                data = slice(data, 0, len);
            }
        }
        return new BinaryValue(data);
    }
}
