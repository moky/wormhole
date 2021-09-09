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
            // TODO: Boyer-Moore Searching
            int index;
            end -= subSize - 1;
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
    };

    // data helper
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
    }
}
