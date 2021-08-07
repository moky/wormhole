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

public interface ByteArray {

    // get inner buffer
    byte[] getBuffer();
    // get view offset
    int getOffset();
    // get view size
    int getSize();

    String toHexString();

    boolean equals(ByteArray other);
    boolean equals(byte[] other);
    boolean equals(byte[] otherBuffer, int otherOffset, int otherCount);

    /**
     *  Get item value with position
     *
     * @param index - position
     * @return item value
     */
    byte getByte(int index);

    /**
     *  Get bytes from inner buffer with range [offset, offset + length)
     *
     * @return data bytes
     */
    byte[] getBytes();
    byte[] getBytes(int start);
    byte[] getBytes(int start, int end);

    ByteArray slice(int start);
    ByteArray slice(int start, int end);

    ByteArray concat(byte[]... others);
    ByteArray concat(ByteArray... others);

    /**
     *  Search value in range [start, end)
     *
     * @param value - element value
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return -1 on not found
     */
    int find(byte value, int start, int end);
    int find(byte value, int start);
    int find(byte value);

    int find(int value, int start, int end);
    int find(int value, int start);
    int find(int value);

    /**
     *  Search sub bytes in range [start, end)
     *
     * @param bytes - sub view
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return -1 on not found
     */
    int find(byte[] bytes, int start, int end);
    int find(byte[] bytes, int start);
    int find(byte[] bytes);

    int find(ByteArray sub, int start, int end);
    int find(ByteArray sub, int start);
    int find(ByteArray sub);

    //
    //  helper
    //

    static String hexEncode(byte[] buffer, int offset, int size) {
        return helper.hexEncode(buffer, offset, size);
    }

    // adjust the position within range [0, len)
    static int adjust(int pos, int len) {
        return helper.adjust(pos, len);
    }
    static int adjustE(int pos, int len) {
        return helper.adjustE(pos, len);
    }

    static ByteArray slice(ByteArray data, int start, int end) {
        return helper.slice(data, start, end);
    }
    static byte[] slice(byte[] bytes, int start, int end) {
        return helper.slice(bytes, start, end);
    }

    static ByteArray concat(ByteArray left, ByteArray right) {
        return helper.concat(left, right);
    }
    static byte[] concat(byte[] leftBuffer, int leftOffset, int leftSize,
                         byte[] rightBuffer, int rightOffset, int rightSize) {
        // create new data and copy left + right
        return helper.concat(leftBuffer, leftOffset, leftSize, rightBuffer, rightOffset, rightSize);
    }

    static int find(ByteArray data, byte value, int start, int end) {
        return helper.find(data, value, start, end);
    }

    static int find(ByteArray data, byte[] subBuffer, int subOffset, int subSize, int start, int end) {
        return helper.find(data, subBuffer, subOffset, subSize, start, end);
    }

    //
    //  Mutable Data
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

        private final char[] HEX_CHARS = {
                '0', '1', '2', '3', '4', '5', '6', '7',
                '8', '9', 'A', 'B', 'C', 'D', 'E', 'F',
        };

        @Override
        public String hexEncode(byte[] buffer, int offset, int size) {
            if (size < 1) {
                return "";
            }
            StringBuilder sb = new StringBuilder(size << 1);
            int pos = offset;
            int end = offset + size;
            byte ch;
            for (; pos < end; ++pos) {
                ch = buffer[pos];
                sb.append(HEX_CHARS[(ch & 0xF0) >> 4]);
                sb.append(HEX_CHARS[ch & 0x0F]);
            }
            return sb.toString();
        }

        @Override
        public int adjust(int pos, int len) {
            if (pos < 0) {
                pos += len;    // count from right hand
                if (pos < 0) {
                    return 0;  // too small
                }
            } else if (pos > len) {
                return len;    // too big
            }
            return pos;
        }

        @Override
        public int adjustE(int pos, int len) {
            if (pos < 0) {
                pos += len;    // count from right hand
                if (pos < 0) {
                    throw new ArrayIndexOutOfBoundsException("error position: " + (pos - len) + ", length: " + len);
                }
            }
            return pos;
        }

        @Override
        public ByteArray slice(ByteArray data, int start, int end) {
            if (start == 0 && end == data.getSize()) {
                // whole data
                return data;
            } else if (start < end) {
                // sub view
                return new Data(data.getBuffer(), data.getOffset() + start, end - start);
            } else {
                // error
                return Data.ZERO;
            }
        }

        @Override
        public byte[] slice(byte[] bytes, int start, int end) {
            if (start == 0 && end == bytes.length) {
                // whole buffer
                return bytes;
            } else if (start < end) {
                // sub buffer
                byte[] sub = new byte[end - start];
                System.arraycopy(bytes, start, sub, 0, end - start);
                return sub;
            } else {
                // error
                return new byte[0];
            }
        }

        @Override
        public ByteArray concat(ByteArray left, ByteArray right) {
            if (right.getSize() == 0) {
                // right is empty, return left directly
                return left;
            } else if (left.getSize() == 0) {
                // left is empty, return right directly
                return right;
            } else if (left.getBuffer() == right.getBuffer() && (left.getOffset() + left.getSize()) == right.getOffset()) {
                // sticky data, create new data on the same buffer
                return new Data(left.getBuffer(), left.getOffset(), left.getSize() + right.getSize());
            } else {
                // create new data and copy left + right
                return new Data(concat(left.getBuffer(), left.getOffset(), left.getSize(),
                        right.getBuffer(), right.getOffset(), right.getSize()));
            }
        }

        @Override
        public byte[] concat(byte[] leftBuffer, int leftOffset, int leftSize, byte[] rightBuffer, int rightOffset, int rightSize) {
            byte[] joined = new byte[leftSize + rightSize];
            System.arraycopy(leftBuffer, leftOffset, joined, 0, leftSize);
            System.arraycopy(rightBuffer, rightOffset, joined, leftSize, rightSize);
            return joined;
        }

        @Override
        public int find(ByteArray data, byte value, int start, int end) {
            byte[] buffer = data.getBuffer();
            start += data.getOffset();
            end += data.getOffset();
            for (; start < end; ++start) {
                if (buffer[start] == value) {
                    // got it
                    return start - data.getOffset();
                }
            }
            return -1;
        }

        @Override
        public int find(ByteArray data, byte[] subBuffer, int subOffset, int subSize, int start, int end) {
            assert subOffset >= 0 : "sub view offset error: " + subOffset;
            assert subSize >= 0 : "sub view size error: " + subSize;
            assert start < end : "search range error: [" + start + ", " + end + ")";
            if ((end - start) < subSize || subSize <= 0) {
                return -1;
            } else if (subSize > 1) {
                end -= subSize - 1;
            }
            byte[] buffer = data.getBuffer();
            start += data.getOffset();
            end += data.getOffset();
            int found = -1;
            if (buffer == subBuffer) {
                // same buffer
                if (start == subOffset) {
                    // the sub.offset matched the start position,
                    // it's surely the first position the sub data appeared.
                    return start - data.getOffset();
                }
                if (start < subOffset && subOffset <= (end - subSize)) {
                    // if sub.offset is in range (start, end - sub.size],
                    // the position (sub.offset - this.offset) is matched,
                    // but we cannot confirm this is the first position the sub data appeared,
                    // so we still need to do searching in range [start, sub.offset + sub.size).
                    found = subOffset - data.getOffset();
                    end = subOffset + subSize - 1;
                }
            }
            int index;
            for (; start < end; ++start) {
                for (index = 0; index < subSize; ++index) {
                    if (buffer[start + index] != subBuffer[subOffset + index]) {
                        // not match
                        break;
                    }
                }
                if (index == subSize) {
                    // got it
                    return start - data.getOffset();
                }
            }
            return found;
        }

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

    interface Helper {

        String hexEncode(byte[] buffer, int offset, int size);

        int adjust(int pos, int len);
        int adjustE(int pos, int len);

        /**
         *  Get bytes within range [start, end)
         *
         * @param data  - data view
         * @param start - start position (include)
         * @param end   - end position (exclude)
         * @return sub bytes
         */
        ByteArray slice(ByteArray data, int start, int end);
        byte[] slice(byte[] bytes, int start, int end);

        ByteArray concat(ByteArray left, ByteArray right);
        byte[] concat(byte[] leftBuffer, int leftOffset, int leftSize,
                      byte[] rightBuffer, int rightOffset, int rightSize);

        /**
         *  Search value in range [start, end)
         *
         * @param data  - this data object
         * @param value - element value
         * @param start - start position (include)
         * @param end   - end position (exclude)
         * @return -1 on not found
         */
        int find(ByteArray data, byte value, int start, int end);

        /**
         *  Search sub view in range [start, end)
         *
         * @param data      - this data object
         * @param subBuffer - sub data buffer
         * @param subOffset - sub view offset
         * @param subSize   - sub view size
         * @param start     - start position (include)
         * @param end       - end position (exclude)
         * @return -1 on not found
         */
        int find(ByteArray data, byte[] subBuffer, int subOffset, int subSize, int start, int end);

        //
        //  mutable
        //

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
