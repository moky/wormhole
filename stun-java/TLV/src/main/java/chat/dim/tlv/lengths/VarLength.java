/* license: https://mit-license.org
 *
 *  TLV: Tag Length Value
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
package chat.dim.tlv.lengths;

import chat.dim.tlv.Length;
import chat.dim.tlv.Tag;
import chat.dim.type.ByteArray;
import chat.dim.type.VarIntData;

/**
 *  Variable Length
 *  ~~~~~~~~~~~~~~~
 */
public class VarLength extends VarIntData implements Length {

    public static final VarLength ZERO = from(VarIntData.ZERO);

    public VarLength(VarIntData data) {
        super(data, data.value);
    }

    public VarLength(ByteArray data, long value) {
        super(data, value);
    }

    //
    //  Factories
    //

    public static VarLength from(VarLength length) {
        return length;
    }

    public static VarLength from(VarIntData data) {
        return new VarLength(data, data.value);
    }

    public static VarLength from(ByteArray data) {
        VarIntData var = VarIntData.from(data);
        return var == null ? null : new VarLength(var);
    }

    public static VarLength from(int value) {
        return new VarLength(VarIntData.from(value));
    }
    public static VarLength from(long value) {
        return new VarLength(VarIntData.from(value));
    }
    public static VarLength from(Integer value) {
        return new VarLength(VarIntData.from(value));
    }
    public static VarLength from(Long value) {
        return new VarLength(VarIntData.from(value));
    }

    // parse length with tag
    public static Length parse(ByteArray data, Tag tag) {
        return from(data);
    }
}
