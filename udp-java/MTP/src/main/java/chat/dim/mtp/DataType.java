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
package chat.dim.mtp;

import java.util.HashMap;
import java.util.Map;

import chat.dim.type.ByteArray;
import chat.dim.type.UInt8Data;

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
 *        Command Response         : 0x01 (0000 0001)
 *        Message                  : 0x02 (0000 0010)
 *        Message Response         : 0x03 (0000 0011)
 *        Message Fragment         : 0x0A (0000 1010)
 */
public final class DataType extends UInt8Data {

    private final String name;

    private DataType(ByteArray data, String name) {
        super(data);
        this.name = name;
    }

    public boolean isResponse() {
        return (value & 0x01) != 0;
    }
    public boolean isFragment() {
        return (value & 0x08) != 0;
    }

    public boolean isCommand() {
        return (value & 0x0F) == 0x00;
    }
    public boolean isCommandResponse() {
        return (value & 0x0F) == 0x01;
    }

    public boolean isMessage() {
        return (value & 0x0F) == 0x02;
    }
    public boolean isMessageResponse() {
        return (value & 0x0F) == 0x03;
    }
    public boolean isMessageFragment() {
        return (value & 0x0F) == 0x0A;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        } else if (other instanceof UInt8Data) {
            return equals(((UInt8Data) other).value);
        } else if (other instanceof Number) {
            return equals(((Number) other).intValue());
        } else {
            return false;
        }
    }
    public boolean equals(int other) {
        return (value & 0x0F) == (other & 0x0F);
    }

    @Override
    public String toString() {
        return name;
    }

    //
    //  Factories
    //

    public static DataType from(UInt8Data ui8) {
        return get(ui8);
    }

    public static DataType from(ByteArray data) {
        UInt8Data ui8 = UInt8Data.from(data);
        return ui8 == null ? null : get(ui8);
    }

    public static DataType from(byte value) {
        return get(UInt8Data.from(value));
    }

    public static DataType from(int value) {
        return get(UInt8Data.from(value));
    }

    private static DataType get(UInt8Data data) {
        byte value = (byte) (data.getByteValue() & 0x0F);
        DataType fixed = s_types.get(value);
        return fixed == null ? null : new DataType(data, fixed.name);
    }

    private static DataType create(int value, String name) {
        UInt8Data data = UInt8Data.from(value);
        DataType type = new DataType(data, name);
        s_types.put(data.getByteValue(), type);
        return type;
    }

    private static final Map<Byte, DataType> s_types = new HashMap<>();

    public static final DataType COMMAND          = create(0x00, "Command");
    public static final DataType COMMAND_RESPONSE = create(0x01, "Command Response");
    public static final DataType MESSAGE          = create(0x02, "Message");
    public static final DataType MESSAGE_RESPONSE = create(0x03, "Message Response");
    public static final DataType MESSAGE_FRAGMENT = create(0x0A, "Message Fragment");
}
