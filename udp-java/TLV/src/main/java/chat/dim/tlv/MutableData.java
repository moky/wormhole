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

public class MutableData extends Data {

    public MutableData(Data data) {
        super(data);
    }

    public MutableData(byte[] bytes) {
        super(bytes);
    }

    public MutableData(byte[] bytes, int offset, int length) {
        super(bytes, offset, length);
    }

    public MutableData(int capacity) {
        this(new byte[capacity], 0, 0);
    }

    /**
     *  Copy buffer values
     *
     * @param src     - source
     * @param srcPos  - source position
     * @param destPos - destination position
     * @param len     - length
     */
    public void copy(Data src, int srcPos, int destPos, int len) {
        if (len <= 0) {
            return;
        }
        // adjust positions
        srcPos = adjust(srcPos, src.length);
        destPos = adjust(destPos, length);
        // adjust length
        if (len > src.length - srcPos) {
            len = src.length - srcPos;
        }
        if (len > length - destPos) {
            len = length - destPos;
        }
        // copy buffer
        System.arraycopy(src.buffer, src.offset + srcPos, buffer, offset + destPos, len);
    }

    public void copy(byte[] src, int srcPos, int destPos, int len) {
        if (len <= 0) {
            return;
        }
        // adjust positions
        srcPos = adjust(srcPos, src.length);
        destPos = adjust(destPos, length);
        // adjust length
        if (len > src.length - srcPos) {
            len = src.length - srcPos;
        }
        if (len > length - destPos) {
            len = length - destPos;
        }
        // copy buffer
        System.arraycopy(src, srcPos, buffer, offset + destPos, len);
    }

    /**
     *  Change byte value at this position
     *
     * @param index - position
     * @param value - byte value
     */
    public boolean setByte(int index, int value) {
        if (index < 0) {
            index += length;   // count from right hand
            if (index < 0) {
                return false;  // too small
            }
        } else if (index >= length) {
            // check buffer size
            int size = offset + index + 1;
            if (size > bufLength) {
                // expends
                byte[] bytes = new byte[size];
                System.arraycopy(buffer, 0, bytes, 0, bufLength);
                buffer = bytes;
                bufLength = size;
            }
            length = index + 1;
        }
        buffer[offset + index] = (byte) (value & 0xFF);
        return true;
    }

    //
    //  Expanding
    //

    public boolean insert(int index, byte value) {
        // check position
        if (index < 0) {
            index += length; // count from right hand
            if (index < 0) {
                throw new ArrayIndexOutOfBoundsException("index error: " + (index - length) + ", length: " + length);
            }
        }
        if (offset > 0) {
            // empty spaces exist before the queue
            if (index == 0) {
                // just insert to the head, no need to move elements
                --offset;
                ++length;
                buffer[offset] = value;
            } else if (index < length) {
                // move left part
                System.arraycopy(buffer, offset, buffer, offset - 1, index);
                buffer[offset + index] = value;
                --offset;
                ++length;
            } else if (offset + index < bufLength){
                // empty spaces exist after the queue,
                // just insert to the tail, no need to move elements
                buffer[offset + index] = value;
                length = index + 1;
            } else {
                // index out of the range, insert directly
                return setByte(index, value);
            }
        } else if (index < length) {
            // check empty spaces
            if (length >= bufLength) {
                expends();
            }
            // move right part
            System.arraycopy(buffer, index, buffer, index + 1, length - index);
            buffer[index] = value;
            ++length;
        } else {
            // index out of the range, insert directly
            return setByte(index, value);
        }
        return true;
    }

    private void expends() {
        int size;
        if (bufLength > 4) {
            size = bufLength << 1;
        } else {
            size = 8;
        }
        byte[] bytes = new byte[size];
        System.arraycopy(buffer, 0, bytes, 0, bufLength);
        buffer = bytes;
        bufLength = size;
    }

    public MutableData append(byte element) {
        int index = offset + length;
        if (index >= bufLength) {
            expends();
        }
        buffer[index] = element;
        ++length;
        return this;
    }

    public MutableData append(int value) {
        return append((byte) (value & 0xFF));
    }

    //
    //  Erasing
    //

    public byte remove(int index) {
        // check position
        if (index < 0) {
            index += length; // count from right hand
            if (index < 0) {
                throw new ArrayIndexOutOfBoundsException("index error: " + (index - length) + ", length: " + length);
            }
        } else if (index >= length) {
            throw new ArrayIndexOutOfBoundsException("index error: " + index + ", length: " + length);
        }
        byte erased = buffer[index];
        System.arraycopy(buffer, index + 1, buffer, index, length - index - 1);
        /*
        int end = offset + length;
        while (index < end) {
            buffer[index] = buffer[++index];
        }
         */
        return erased;
    }

    public byte shift() {
        if (length <= 0) {
            throw new ArrayIndexOutOfBoundsException("data empty!");
        }
        byte erased = buffer[offset];
        ++offset;
        --length;
        return erased;
    }

    public byte pop() {
        if (length <= 0) {
            throw new ArrayIndexOutOfBoundsException("data empty!");
        }
        --length;
        return buffer[offset + length];
    }
}
