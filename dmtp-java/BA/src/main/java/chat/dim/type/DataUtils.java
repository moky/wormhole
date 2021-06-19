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

final class DataUtils {

    // adjust the position within range [0, len)
    static int adjust(int pos, int len) {
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
    static int adjustE(int pos, int len) {
        if (pos < 0) {
            pos += len;  // count from right hand
            if (pos < 0) {
                throw new ArrayIndexOutOfBoundsException("error position: " + (pos - len) + ", length: " + len);
            }
        }
        return pos;
    }

    static Data slice(Data data, int start, int end) {
        if (start == 0 && end == data.length) {
            // whole data
            return data;
        } else if (start < end) {
            // sub view
            return new Data(data.buffer, data.offset + start, end - start);
        } else {
            // error
            return Data.ZERO;
        }
    }

    static Data concat(Data left, Data right) {
        if (left.length == 0) {
            return right;
        } else if (right.length == 0) {
            return left;
        } else if (left.buffer == right.buffer && (left.offset + left.length) == right.offset) {
            // sticky data
            return new Data(left.buffer, left.offset, left.length + right.length);
        } else {
            byte[] joined = new byte[left.length + right.length];
            System.arraycopy(left.buffer, left.offset, joined, 0, left.length);
            System.arraycopy(right.buffer, right.offset, joined, left.length, right.length);
            return new Data(joined);
        }
    }

    /**
     *  Search value in range [start, end)
     *
     * @param data  - this data object
     * @param value - element value
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return -1 on not found
     */
    static int find(Data data, byte value, int start, int end) {
        start += data.offset;
        end += data.offset;
        for (; start < end; ++start) {
            if (data.buffer[start] == value) {
                // got it
                return start - data.offset;
            }
        }
        return -1;
    }

    /**
     *  Search sub view in range [start, end)
     *
     * @param data      - this data object
     * @param subBuffer - sub data buffer
     * @param subOffset - sub data offset
     * @param subLength - sub data length
     * @param start     - start position (include)
     * @param end       - end position (exclude)
     * @return -1 on not found
     */
    static int find(Data data, byte[] subBuffer, int subOffset, int subLength, int start, int end) {
        assert subOffset >= 0 : "sub data offset error: " + subOffset;
        assert subLength >= 0 : "sub data length error: " + subLength;
        assert start < end : "search range error: [" + start + ", " + end + ")";
        if ((end - start) < subLength || subLength <= 0) {
            return -1;
        }
        start += data.offset;
        end += data.offset - subLength + 1;
        int found = -1;
        if (data.buffer == subBuffer) {
            // same buffer
            if (start == subOffset) {
                return start - data.offset;
            }
            if (start < subOffset && subOffset < end) {
                // if sub.offset is in range (start, end),
                // the position (sub.offset - this.offset) is matched,
                // but we cannot confirm this is the first position it appeared,
                // so we still need to do searching in range [start, sub.offset).
                found = subOffset - data.offset;
                end = subOffset;
            }
        }
        int index;
        for (; start < end; ++start) {
            for (index = 0; index < subLength; ++index) {
                if (data.buffer[start + index] != subBuffer[subOffset + index]) {
                    // not match
                    break;
                }
            }
            if (index == subLength) {
                // got it
                return start - data.offset;
            }
        }
        return found;
    }

    /**
     *  Get bytes within range [start, end)
     *
     * @param data  - this data object
     * @param start - start position (include)
     * @param end   - end position (exclude)
     * @return sub bytes
     */
    static byte[] getBytes(Data data, int start, int end) {
        start += data.offset;
        end += data.offset;
        // check range
        if (start == 0 && end == data.buffer.length) {
            // whole buffer
            return data.buffer;
        } else if (start < end) {
            // copy sub-array
            int copyLen = end - start;
            byte[] bytes = new byte[copyLen];
            System.arraycopy(data.buffer, start, bytes, 0, copyLen);
            return bytes;
        } else {
            // empty buffer
            return Data.ZERO.getBytes();
        }
    }

    //
    //  Mutable Data
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
    static void update(MutableData data, int index, byte[] source, int start, int end) {
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
                    System.arraycopy(data.buffer, data.offset, data.buffer, 0, data.length);
                    data.offset = 0;
                }
            }
            // copy source buffer
            System.arraycopy(source, start, data.buffer, data.offset + index, copyLen);
        }
        // reset view length
        if (copyEnd > data.length) {
            data.length = copyEnd;
        }
    }

    /**
     *  Insert values from source buffer with range [start, end)
     *
     * @param data   - this mutable data object
     * @param index  - copy to self buffer from this relative position
     * @param source - source buffer
     * @param start  - source start position (include)
     * @param end    - source end position (exclude)
     */
    static void insert(MutableData data, int index, byte[] source, int start, int end) {
        assert index >= 0 : "insert index error: " + index;
        assert start >= 0 & end <= source.length :
                "source range error: [" + start + ", " + end + "), size: " + source.length;
        int copyLen = end - start;
        assert copyLen > 0 : "source range error: [" + start + ", " + end + ")";
        int newLen;
        if (index < data.length) {
            newLen = data.length + copyLen;
        } else {
            // target position out of range [0, length)
            newLen = index + copyLen;
        }
        if (data.buffer == source || newLen > data.buffer.length) {
            // just expend the buffer if it is same to source buffer,
            // even though empty spaces are enough
            data.resize(newLen);
        } else if (index < (data.length >> 1)) {
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
                if (index < data.length) {
                    // move the right part (steps: copyLen)
                    System.arraycopy(data.buffer, data.offset + index,
                            data.buffer, data.offset + index + copyLen, data.length - index);
                }
            } else {
                // move left part
                System.arraycopy(data.buffer, data.offset, data.buffer, 0, index);
                // move the right part
                System.arraycopy(data.buffer, data.offset + index,
                        data.buffer, index + copyLen, data.length - index);
                data.offset = 0;
            }
        } else {
            // target position is near the tail?
            if ((data.offset + newLen) < data.buffer.length) {
                // right spaces are enough
                if (index < data.length) {
                    // move the right part (steps: copyLen)
                    System.arraycopy(data.buffer, data.offset + index,
                            data.buffer, data.offset + index + copyLen, data.length - index);
                }
            } else if (data.offset >= (newLen - data.length)) {
                // left spaces are enough, move left part/whole data (steps: -copyLen)
                System.arraycopy(data.buffer, data.offset,
                        data.buffer, data.offset - copyLen, Math.min(index, data.length));
                data.offset -= copyLen;
            } else if (index < data.length) {
                // move left part
                System.arraycopy(data.buffer, data.offset, data.buffer, 0, index);
                // move the right part
                System.arraycopy(data.buffer, data.offset + index,
                        data.buffer, index + copyLen, data.length - index);
                data.offset = 0;
            } else {
                // move the whole buffer
                System.arraycopy(data.buffer, data.offset, data.buffer, 0, data.length);
                data.offset = 0;
            }
        }
        // copy source buffer
        System.arraycopy(source, start, data.buffer, data.offset + index, copyLen);
        data.length = newLen;
    }

    /**
     *  Insert the value to this position
     *
     * @param data  - this mutable data object
     * @param index - position
     * @param value - byte value
     */
    static void insert(MutableData data, int index, byte value) {
        assert 0 <= index && index < data.length : "index out of range: " + index + ", " + data.length;
        if (index == 0) {
            // insert to the head
            if (data.offset > 0) {
                // empty spaces exist before the queue, no need to move elements
                data.offset -= 1;
            } else {
                // no empty space before the queue
                if (data.length >= data.buffer.length) {
                    // the buffer is full, expand it
                    data.expands();
                }
                // move the queue to right
                System.arraycopy(data.buffer, 0, data.buffer, 1, data.length);
            }
        } else if (index < (data.length >> 1)) {
            // target position is near the head
            if (data.offset > 0) {
                // empty spaces found before the queue, move the left part
                System.arraycopy(data.buffer, data.offset, data.buffer, data.offset - 1, index);
                data.offset -= 1;
            } else {
                // no empty space before the queue
                if (data.length >= data.buffer.length) {
                    // the space is full, expand it
                    data.expands();
                }
                // move the right part
                System.arraycopy(data.buffer, data.offset + index,
                        data.buffer, data.offset + index + 1, data.length - index);
            }
        } else {
            // target position is near the tail
            if ((data.offset + data.length) < data.buffer.length) {
                // empty spaces found after the queue, move the right part
                System.arraycopy(data.buffer, data.offset + index,
                        data.buffer, data.offset + index + 1, data.length - index);
            } else if (data.offset > 0) {
                // empty spaces found before the queue, move the left part
                System.arraycopy(data.buffer, data.offset, data.buffer, data.offset - 1, index);
                data.offset -= 1;
            } else {
                // the space is full, expand it
                data.expands();
                // move the right part
                System.arraycopy(data.buffer, data.offset + index,
                        data.buffer, data.offset + index + 1, data.length - index);
            }
        }
        data.buffer[data.offset + index] = value;
        data.length += 1;
    }

    /**
     *  Remove element at this position and return its value
     *
     * @param data  - this mutable data object
     * @param index - position
     * @return element value removed
     */
    static byte remove(MutableData data, int index) {
        assert 0 < index && index < (data.length - 1) : "index out of range: " + index + ", " + data.length;
        // remove inside element
        byte erased = data.buffer[data.offset + index];
        if (index < (data.length >> 1)) {
            // target position is near the head, move the left part
            System.arraycopy(data.buffer, data.offset, data.buffer, data.offset + 1, index);
            data.offset += 1;
        } else {
            // target position is near the tail, move the right part
            System.arraycopy(data.buffer, data.offset + index + 1,
                    data.buffer, data.offset + index, data.length - index - 1);
        }
        data.length -= 1;
        return erased;
    }
}
