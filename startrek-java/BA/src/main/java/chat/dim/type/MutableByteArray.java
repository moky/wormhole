/* license: https://mit-license.org
 *
 *  BA: Byte Array
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
package chat.dim.type;

public interface MutableByteArray extends ByteArray {

    /**
     * Change byte value at this position
     *
     * @param index - position
     * @param value - byte value
     */
    void setByte(int index, byte value);
    void setChar(int index, char value);

    /**
     *  Update values from source buffer with range [start, end)
     *
     * @param index  - update buffer from this relative position
     * @param source - source buffer
     * @param start  - source start position (include)
     * @param end    - source end position (exclude)
     */
    void update(int index, byte[] source, int start, int end);
    void update(int index, byte[] source, int start);
    void update(int index, byte[] source);

    void update(int index, ByteArray source, int start, int end);
    void update(int index, ByteArray source, int start);
    void update(int index, ByteArray source);

    /**
     *  Append values from source buffer with range [start, end)
     *
     * @param source - source buffer
     * @param start  - source start position (include)
     * @param end    - source end position (exclude)
     */
    void append(byte[] source, int start, int end);
    void append(byte[] source, int start);
    void append(byte[] source);
    void append(byte[]... sources);

    void append(ByteArray source, int start, int end);
    void append(ByteArray source, int start);
    void append(ByteArray source);
    void append(ByteArray... sources);

    /**
     *  Insert values from source buffer with range [start, end)
     *
     * @param index  - insert buffer from this relative position
     * @param source - source buffer
     * @param start  - source start position (include)
     * @param end    - source end position (exclude)
     */
    void insert(int index, byte[] source, int start, int end);
    void insert(int index, byte[] source, int start);
    void insert(int index, byte[] source);

    void insert(int index, ByteArray source, int start, int end);
    void insert(int index, ByteArray source, int start);
    void insert(int index, ByteArray source);

    /**
     *  Insert the value to this position
     *
     * @param index - position
     * @param value - byte value
     */
    void insert(int index, byte value);

    /**
     *  Remove element at this position and return its value
     *
     * @param index - position
     * @return element value removed
     * @throws ArrayIndexOutOfBoundsException on error
     */
    byte remove(int index);

    /**
     *  Remove element from the head position and return its value
     *
     * @return element value at the first place
     * @throws ArrayIndexOutOfBoundsException on data empty
     */
    byte shift();

    /**
     *  Remove element from the tail position and return its value
     *
     * @return element value at the last place
     * @throws ArrayIndexOutOfBoundsException on data empty
     */
    byte pop();

    /**
     *  Append the element to the tail
     *
     * @param element - value
     */
    void append(char element);
    void append(byte element);
    void push(byte element);

    //
    //  helper
    //

    static void update(MutableData data, int index, byte[] source, int start, int end) {
        helper.update(data, index, source, start, end);
    }

    static void insert(MutableData data, int index, byte[] source, int start, int end) {
        helper.insert(data, index, source, start, end);
    }
    static void insert(MutableData data, int index, byte value) {
        helper.insert(data, index, value);
    }

    static byte remove(MutableData data, int index) {
        return helper.remove(data, index);
    }

    // default helper
    Helper helper = new Helper() {

        @Override
        public void update(MutableData data, int index, byte[] source, int start, int end) {
            assert index >= 0 : "update index error: " + index;
            assert start >= 0 & end <= source.length :
                    "source range error: [" + start + ", " + end + "), size: " + source.length;
            int copyLen = end - start;
            assert copyLen > 0 : "source range error: [" + start + ", " + end + ")";
            int copyEnd = index + copyLen;
            if (source != data.buffer || (data.offset + index) != start) {
                // not sticky data
                if ((data.offset + copyEnd) > data.buffer.length) {
                    // not enough spaces on the right hand
                    if (source == data.buffer || copyEnd > data.buffer.length) {
                        // just expend the buffer if it is same to source buffer,
                        // even though empty spaces on the left hand are enough
                        data.resize(copyEnd);
                    } else {
                        // move data to left
                        System.arraycopy(data.buffer, data.offset, data.buffer, 0, data.size);
                        data.offset = 0;
                    }
                }
                // copy source buffer
                System.arraycopy(source, start, data.buffer, data.offset + index, copyLen);
            }
            // reset view size
            if (copyEnd > data.size) {
                data.size = copyEnd;
            }
        }

        @Override
        public void insert(MutableData data, int index, byte[] source, int start, int end) {
            assert index >= 0 : "insert index error: " + index;
            assert start >= 0 & end <= source.length :
                    "source range error: [" + start + ", " + end + "), size: " + source.length;
            int copyLen = end - start;
            assert copyLen > 0 : "source range error: [" + start + ", " + end + ")";
            int newLen;
            if (index < data.size) {
                newLen = data.size + copyLen;
            } else {
                // target position out of range [0, size)
                newLen = index + copyLen;
            }
            if (data.buffer == source || newLen > data.buffer.length) {
                // just expend the buffer if it is same to source buffer,
                // even though empty spaces are enough
                data.resize(newLen);
            } else if (index < (data.size >> 1)) {
                // target position is near the head
                if (data.offset >= copyLen) {
                    // left spaces are enough
                    if (index > 0) {
                        // move left part (steps: -copyLen)
                        System.arraycopy(data.buffer, data.offset, data.buffer, data.offset - copyLen, index);
                    }
                    data.offset -= copyLen;
                } else if ((data.offset + newLen) < data.buffer.length) {
                    // right spaces are enough
                    if (index < data.size) {
                        // move the right part (steps: copyLen)
                        System.arraycopy(data.buffer, data.offset + index,
                                data.buffer, data.offset + index + copyLen, data.size - index);
                    }
                } else {
                    // move left part
                    System.arraycopy(data.buffer, data.offset, data.buffer, 0, index);
                    // move the right part
                    System.arraycopy(data.buffer, data.offset + index,
                            data.buffer, index + copyLen, data.size - index);
                    data.offset = 0;
                }
            } else {
                // target position is near the tail?
                if ((data.offset + newLen) < data.buffer.length) {
                    // right spaces are enough
                    if (index < data.size) {
                        // move the right part (steps: copyLen)
                        System.arraycopy(data.buffer, data.offset + index,
                                data.buffer, data.offset + index + copyLen, data.size - index);
                    }
                } else if (data.offset >= (newLen - data.size)) {
                    // left spaces are enough, move left part/whole data (steps: -copyLen)
                    System.arraycopy(data.buffer, data.offset,
                            data.buffer, data.offset - copyLen, Math.min(index, data.size));
                    data.offset -= copyLen;
                } else if (index < data.size) {
                    // move left part
                    System.arraycopy(data.buffer, data.offset, data.buffer, 0, index);
                    // move the right part
                    System.arraycopy(data.buffer, data.offset + index,
                            data.buffer, index + copyLen, data.size - index);
                    data.offset = 0;
                } else {
                    // move the whole buffer
                    System.arraycopy(data.buffer, data.offset, data.buffer, 0, data.size);
                    data.offset = 0;
                }
            }
            // copy source buffer
            System.arraycopy(source, start, data.buffer, data.offset + index, copyLen);
            data.size = newLen;
        }

        @Override
        public void insert(MutableData data, int index, byte value) {
            assert 0 <= index && index < data.size : "index out of range: " + index + ", " + data.size;
            if (index == 0) {
                // insert to the head
                if (data.offset > 0) {
                    // empty spaces exist before the queue, no need to move elements
                    data.offset -= 1;
                } else {
                    // no empty space before the queue
                    if (data.size >= data.buffer.length) {
                        // the buffer is full, expand it
                        data.expands();
                    }
                    // move the queue to right
                    System.arraycopy(data.buffer, 0, data.buffer, 1, data.size);
                }
            } else if (index < (data.size >> 1)) {
                // target position is near the head
                if (data.offset > 0) {
                    // empty spaces found before the queue, move the left part
                    System.arraycopy(data.buffer, data.offset, data.buffer, data.offset - 1, index);
                    data.offset -= 1;
                } else {
                    // no empty space before the queue
                    if (data.size >= data.buffer.length) {
                        // the space is full, expand it
                        data.expands();
                    }
                    // move the right part
                    System.arraycopy(data.buffer, data.offset + index,
                            data.buffer, data.offset + index + 1, data.size - index);
                }
            } else {
                // target position is near the tail
                if ((data.offset + data.size) < data.buffer.length) {
                    // empty spaces found after the queue, move the right part
                    System.arraycopy(data.buffer, data.offset + index,
                            data.buffer, data.offset + index + 1, data.size - index);
                } else if (data.offset > 0) {
                    // empty spaces found before the queue, move the left part
                    System.arraycopy(data.buffer, data.offset, data.buffer, data.offset - 1, index);
                    data.offset -= 1;
                } else {
                    // the space is full, expand it
                    data.expands();
                    // move the right part
                    System.arraycopy(data.buffer, data.offset + index,
                            data.buffer, data.offset + index + 1, data.size - index);
                }
            }
            data.buffer[data.offset + index] = value;
            data.size += 1;
        }

        @Override
        public byte remove(MutableData data, int index) {
            assert 0 < index && index < (data.size - 1) : "index out of range: " + index + ", " + data.size;
            // remove inside element
            byte erased = data.buffer[data.offset + index];
            if (index < (data.size >> 1)) {
                // target position is near the head, move the left part
                System.arraycopy(data.buffer, data.offset, data.buffer, data.offset + 1, index);
                data.offset += 1;
            } else {
                // target position is near the tail, move the right part
                System.arraycopy(data.buffer, data.offset + index + 1,
                        data.buffer, data.offset + index, data.size - index - 1);
            }
            data.size -= 1;
            return erased;
        }
    };

    // mutable data helper
    interface Helper {

        /**
         *  Copy values from source buffer with range [start, end)
         *
         * @param data   - this mutable data object
         * @param index  - copy to self buffer from this relative position
         * @param source - source buffer
         * @param start  - source start position (include)
         * @param end    - source end position (exclude)
         */
        void update(MutableData data, int index, byte[] source, int start, int end);

        /**
         *  Insert values from source buffer with range [start, end)
         *
         * @param data   - this mutable data object
         * @param index  - copy to self buffer from this relative position
         * @param source - source buffer
         * @param start  - source start position (include)
         * @param end    - source end position (exclude)
         */
        void insert(MutableData data, int index, byte[] source, int start, int end);

        /**
         *  Insert the value to this position
         *
         * @param data  - this mutable data object
         * @param index - position
         * @param value - byte value
         */
        void insert(MutableData data, int index, byte value);

        /**
         *  Remove element at this position and return its value
         *
         * @param data  - this mutable data object
         * @param index - position
         * @return element value removed
         */
        byte remove(MutableData data, int index);
    }
}
