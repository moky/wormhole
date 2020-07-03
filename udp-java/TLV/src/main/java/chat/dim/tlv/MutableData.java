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

    public MutableData() {
        this(4);
    }

    private void resize(int size) {
        byte[] bytes = new byte[size];
        System.arraycopy(buffer, 0, bytes, 0, bufLength);
        buffer = bytes;
        bufLength = size;
    }

    private void expends() {
        if (bufLength > 4) {
            resize(bufLength << 1);
        } else {
            resize(8);
        }
    }

    //
    //  Updating
    //

    /**
     *  Change byte value at this position
     *
     * @param index - position
     * @param value - byte value
     */
    public boolean setByte(int index, byte value) {
        if (index < 0) {
            index += length;   // count from right hand
            if (index < 0) {
                return false;  // too small
            }
        } else if (index >= length) {
            // check buffer size
            int size = offset + index + 1;
            if (size > bufLength) {
                // expend the buffer to new size
                resize(size);
            }
            length = index + 1;
        }
        buffer[offset + index] = value;
        return true;
    }

    public boolean setByte(int index, int value) {
        return setByte(index, (byte) (value & 0xFF));
    }

    /**
     *  Copy values from source buffer with range [start, end)
     *
     * @param index  - copy to self buffer from this position
     * @param source - source buffer
     * @param start  - source start position (include)
     * @param end    - source end position (exclude)
     */
    public MutableData copy(int index, byte[] source, int start, int end) {
        // adjust positions
        if (index < 0) {
            index += length;  // count from right hand
            if (index < 0) {
                throw new ArrayIndexOutOfBoundsException("error index: " + (index - length) + ", length: " + length);
            }
        }
        start = adjust(start, source.length);
        end = adjust(end, source.length);
        if (start < end) {
            if (source == buffer) {
                // same buffer, check neighbours
                if (offset + index == start) {
                    // nothing changed
                    return this;
                }
            }
            int copyLen = end - start;
            int newSize = offset + index + copyLen;
            if (newSize > bufLength) {
                // expend the buffer to this size
                resize(newSize);
            }
            // copy buffer
            System.arraycopy(source, start, buffer, offset + index, copyLen);
            // reset view length
            if (index + copyLen > length) {
                length = index + copyLen;
            }
        }
        return this;
    }

    public MutableData copy(int index, byte[] source, int start) {
        return copy(index, source, start, source.length);
    }

    public MutableData copy(int index, byte[] source) {
        return copy(index, source, 0, source.length);
    }

    public MutableData copy(int index, Data source, int start, int end) {
        // adjust position
        start = adjust(start, source.length);
        end = adjust(end, source.length);
        return copy(index, source.buffer, source.offset + start, source.offset + end);
    }

    public MutableData copy(int index, Data source, int start) {
        return copy(index, source, start, source.length);
    }

    public MutableData copy(int index, Data source) {
        return copy(index, source, 0, source.length);
    }

    //
    //  Expanding
    //

    /**
     *  Insert the value to this position
     *
     * @param index -
     * @param value -
     * @return false for ArrayIndexOutOfBoundsException
     */
    public boolean insert(int index, byte value) {
        // check position
        if (index < 0) {
            index += length; // count from right hand
            if (index < 0) {
                return false;
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

    /**
     *  Append the element to the tail
     *
     * @param element - value
     */
    public MutableData append(byte element) {
        int index = offset + length;
        if (index >= bufLength) {
            // expend the buffer
            expends();
        }
        buffer[index] = element;
        ++length;
        return this;
    }

    public MutableData append(int value) {
        return append((byte) (value & 0xFF));
    }

    /**
     *  Append values from source buffer with range [start, end)
     *
     * @param source - source buffer
     * @param start  - source start position (include)
     * @param end    - source end position (exclude)
     */
    public MutableData append(byte[] source, int start, int end) {
        return copy(length, source, start, end);
    }

    public MutableData append(byte[] source, int start) {
        return copy(length, source, start);
    }

    public MutableData append(byte[] source) {
        return copy(length, source);
    }

    public MutableData append(Data source, int start, int end) {
        return copy(length, source, start, end);
    }

    public MutableData append(Data source, int start) {
        return copy(length, source, start);
    }

    public MutableData append(Data source) {
        return copy(length, source);
    }

    //
    //  Erasing
    //

    /**
     *  Remove element at this position and return its value
     *
     * @param index - position
     * @return element value removed
     * @throws ArrayIndexOutOfBoundsException on error
     */
    public byte remove(int index) {
        // check position
        index = adjustE(index, length);
        if (index >= length) {
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

    /**
     *  Remove element from the head position and return its value
     *
     * @return element value at the first place
     * @throws ArrayIndexOutOfBoundsException on data empty
     */
    public byte shift() {
        if (isEmpty()) {
            throw new ArrayIndexOutOfBoundsException("data empty!");
        }
        byte erased = buffer[offset];
        ++offset;
        --length;
        return erased;
    }

    /**
     *  Remove element from the tail position and return its value
     *
     * @return element value at the last place
     * @throws ArrayIndexOutOfBoundsException on data empty
     */
    public byte pop() {
        if (isEmpty()) {
            throw new ArrayIndexOutOfBoundsException("data empty!");
        }
        --length;
        return buffer[offset + length];
    }

    public boolean isEmpty() {
        return length <= 0;
    }
}
