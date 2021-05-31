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

    public int getCapacity() {
        return buffer.length - offset;
    }

    private static void arraycopy(byte[] src,  int  srcPos,
                                  byte[] dest, int destPos,
                                  int length) {
        if (src == dest) {
            // the src and dest arguments refer to the same array object
            // 'System.arraycopy()' would create a temporary array,
            // to avoid memory waste, we do the job by ourself here.
            if (srcPos < destPos) {
                // move to right
                for (int index = length - 1; index >= 0; --index) {
                    dest[destPos + index] = src[srcPos + index];
                }
            } else if (srcPos > destPos) {
                // move to left
                for (int index = 0; index < length; ++index) {
                    dest[destPos + index] = src[srcPos + index];
                }
            }
        } else {
            System.arraycopy(src, srcPos, dest, destPos, length);
        }
    }

    private void resize(int size) {
        assert size > length : "size too small for old data: size=" + size + ", length=" + length;
        byte[] bytes = new byte[size];
        System.arraycopy(buffer, offset, bytes, 0, length);
        buffer = bytes;
        offset = 0;
    }

    private void expands() {
        int capacity = getCapacity();
        if (capacity > 4) {
            resize(capacity << 1);
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
        // adjust position
        if (index < 0) {
            index += length;   // count from right hand
            if (index < 0) {
                return false;  // too small
                //throw new ArrayIndexOutOfBoundsException("error index: " + (index - length) + ", length: " + length);
            }
        }
        // check position
        if (index >= length) {
            // target position is out of range [offset, offset + length)
            // check empty spaces on the right
            if (offset + index >= buffer.length) {
                // empty spaces on the right not enough
                // check empty spaces on the left
                if (index < buffer.length) {
                    // move all data left
                    arraycopy(buffer, offset, buffer, 0, length);
                    offset = 0;
                } else {
                    // current space not enough, expand it
                    resize(index + 1);
                }
            }
            // TODO: fill range [offset + length, offset + index) with ZERO?
            length = index + 1;
        }
        buffer[offset + index] = value;
        return true;
    }

    /**
     *  Copy values from source buffer with range [start, end)
     *
     * @param pos    - copy to self buffer from this position
     * @param source - source buffer
     * @param start  - source start position (include)
     * @param end    - source end position (exclude)
     */
    private void copyBuffer(int pos, byte[] source, int start, int end) {
        // adjust position
        if (pos < 0) {
            pos += length;  // count from right hand
            if (pos < 0) {
                throw new ArrayIndexOutOfBoundsException("error position: " + (pos - length) + ", length: " + length);
            }
        }
        int copyLen = end - start;
        if (copyLen > 0) {
            int destPos = offset + pos;
            int copyEnd = pos + copyLen;  // relative to offset
            if (source != buffer || destPos != start) {
                // not sticky data
                if (getCapacity() < copyEnd) {
                    // expend the buffer to this size
                    resize(copyEnd);
                }
                // copy buffer
                arraycopy(source, start, buffer, destPos, copyLen);
            }
            // reset view length
            if (copyEnd > length) {
                length = copyEnd;
            }
        }
    }

    public void fill(int pos, byte[] source, int start, int end) {
        start = adjust(start, source.length);
        end = adjust(end, source.length);
        copyBuffer(pos, source, start, end);
    }

    public void fill(int pos, byte[] source, int start) {
        start = adjust(start, source.length);
        copyBuffer(pos, source, start, source.length);
    }

    public void fill(int pos, byte[] source) {
        copyBuffer(pos, source, 0, source.length);
    }

    public void fill(int pos, Data source, int start, int end) {
        start = adjust(start, source.length);
        end = adjust(end, source.length);
        copyBuffer(pos, source.buffer, source.offset + start, source.offset + end);
    }

    public void fill(int pos, Data source, int start) {
        start = adjust(start, source.length);
        copyBuffer(pos, source.buffer, start, source.length);
    }

    public void fill(int pos, Data source) {
        copyBuffer(pos, source.buffer, 0, source.length);
    }

    //
    //  Expanding
    //

    /**
     *  Append values from source buffer with range [start, end)
     *
     * @param source - source buffer
     * @param start  - source start position (include)
     * @param end    - source end position (exclude)
     */
    public void append(byte[] source, int start, int end) {
        fill(length, source, start, end);
    }

    public void append(byte[] source, int start) {
        fill(length, source, start);
    }

    public void append(byte[] source) {
        fill(length, source);
    }

    public void append(Data source, int start, int end) {
        fill(length, source, start, end);
    }

    public void append(Data source, int start) {
        fill(length, source, start);
    }

    public void append(Data source) {
        fill(length, source);
    }

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
            index += length;  // count from right hand
            if (index < 0) {
                return false;  // too small
                //throw new ArrayIndexOutOfBoundsException("error index: " + (index - length) + ", length: " + length);
            }
        }
        if (index >= length) {
            // target position is out of range [offset, offset + length)
            // set it directly
            return setByte(index, value);
        }
        if (index == 0) {
            // insert to the head
            if (offset > 0) {
                // empty spaces exist before the queue, no need to move elements
                offset -= 1;
            } else {
                // no empty space before the queue
                if (length == buffer.length) {
                    // the buffer is full, expand it
                    expands();
                }
                // move the queue to right
                arraycopy(buffer, 0, buffer, 1, length);
            }
        } else if (index < (length >> 1)) {
            // target position is near the head
            if (offset > 0) {
                // empty spaces found before the queue, move left part
                arraycopy(buffer, offset, buffer, offset - 1, index);
                offset -= 1;
            } else {
                if ((offset + length) == buffer.length) {
                    // the space is full, expand it
                    expands();
                }
                // move right part
                arraycopy(buffer, offset + index, buffer, offset + index + 1, length - index);
            }
        } else {
            // target position is near the tail
            if ((offset + length) < buffer.length) {
                // empty spaces found after the queue, move right part
                arraycopy(buffer, offset + index, buffer, offset + index + 1, length - index);
            } else if (offset > 0) {
                // empty spaces found before the queue, move left part
                arraycopy(buffer, offset, buffer, offset - 1, index);
                offset -= 1;
            } else {
                // the space is full, expand it
                expands();
                // move right part
                arraycopy(buffer, offset + index, buffer, offset + index + 1, length - index);
            }
        }
        buffer[offset + index] = value;
        length += 1;
        return true;
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
        // adjust position
        if (index < 0) {
            index += length;  // count from right hand
            if (index < 0) {  // too small
                throw new ArrayIndexOutOfBoundsException("error index: " + (index - length) + ", length: " + length);
            }
        } else if (index >= length) {  // too big
            throw new ArrayIndexOutOfBoundsException("index error: " + index + ", length: " + length);
        }
        if (index == 0) {
            // remove the first element
            return shift();
        } else if (index == (length - 1)) {
            // remove the last element
            return pop();
        } else {
            // remove inside element
            byte erased = buffer[index];
            arraycopy(buffer, index + 1, buffer, index, length - index - 1);
            return erased;
        }
    }

    /**
     *  Remove element from the head position and return its value
     *
     * @return element value at the first place
     * @throws ArrayIndexOutOfBoundsException on data empty
     */
    public byte shift() {
        if (length < 1) {
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
        if (length < 1) {
            throw new ArrayIndexOutOfBoundsException("data empty!");
        }
        --length;
        return buffer[offset + length];
    }

    /**
     *  Append the element to the tail
     *
     * @param element - value
     */
    public void push(byte element) {
        insert(length, element);
    }
}
