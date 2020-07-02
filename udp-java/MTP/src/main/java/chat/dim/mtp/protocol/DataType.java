/* license: https://mit-license.org
 *
 *  MTP: Message Transfer Protocol
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
package chat.dim.mtp.protocol;

import java.util.HashMap;
import java.util.Map;

/*    Data Type:
 *
 *          0   1   2   3   4   5   6   7
 *        +---+---+---+---+---+---+---+---+
 *        |               | F |   | M | A |
 *        |               | R |   | S | C |
 *        |               | G |   | G | K |
 *        +---+---+---+---+---+---+---+---+
 *
 *        Command                  : 0x00 (0000 0000)
 *        Command Respond          : 0x01 (0000 0001)
 *        Message                  : 0x02 (0000 0010)
 *        Message Respond          : 0x03 (0000 0011)
 *        Message Fragment         : 0x0A (0000 1010)
 */
public class DataType {

    public final byte value;
    public final String name;

    public DataType(byte value, String name) {
        super();
        this.value = value;
        this.name = name;
        s_types.put(value, this);
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (other instanceof DataType) {
            return equals(((DataType) other).value);
        }
        return false;
    }
    public boolean equals(int other) {
        return value == other;
    }

    @Override
    public int hashCode() {
        return Integer.hashCode(value);
    }

    //
    //  Factory
    //

    public static synchronized DataType getInstance(byte value) {
        DataType type = s_types.get(value);
        if (type == null) {
            //type = new DataType(value, "DataType-" + Integer.toHexString(value));
            throw new NullPointerException("data type error: " + value);
        }
        return type;
    }

    private static final Map<Byte, DataType> s_types = new HashMap<>();

    public static DataType Command         = new DataType((byte) 0x00, "Command");
    public static DataType CommandRespond  = new DataType((byte) 0x01, "Command Respond");
    public static DataType Message         = new DataType((byte) 0x02, "Message");
    public static DataType MessageRespond  = new DataType((byte) 0x03, "Message Respond");
    public static DataType MessageFragment = new DataType((byte) 0x0A, "Message Fragment");
}
