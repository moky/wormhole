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

public class MutableData extends Data implements MutableByteArray {

    public MutableData(ByteArray data) {
        super(data);
    }

    public MutableData(byte[] bytes) {
        super(bytes);
    }

    public MutableData(byte[] bytes, int offset, int size) {
        super(bytes, offset, size);
    }

    public MutableData(int capacity) {
        this(new byte[capacity], 0, 0);
    }

    public MutableData() {
        this(4);
    }

    void resize(int newSize) {
        assert newSize > size : "size too small for old data: new size=" + newSize + ", view size=" + size;
        byte[] bytes = new byte[newSize];
        System.arraycopy(buffer, offset, bytes, 0, size);
        buffer = bytes;
        offset = 0;
    }

    void expands() {
        int capacity = buffer.length - offset;
        if (capacity > 2) {
            resize(capacity << 1);
        } else {
            resize(4);
        }
    }

    //
    //  Writing
    //

    @Override
    public void setChar(int index, char value) {
        setByte(index, (byte) value);
    }
    @Override
    public void setByte(int index, byte value) {
        index = ByteArray.adjustE(index, size);
        if (index >= size) {
            // target position is out of range [offset, offset + size)
            // check empty spaces
            if (index >= buffer.length) {
                // current space not enough, expand it
                resize(index + 1);
            } else if (offset + index >= buffer.length) {
                // empty spaces on the right not enough
                // move all data left
                System.arraycopy(buffer, offset, buffer, 0, size);
                offset = 0;
            }
            size = index + 1;
        }
        buffer[offset + index] = value;
    }

    //
    //  Updating
    //

    @Override
    public void update(int index, byte[] source, int start, int end) {
        start = ByteArray.adjust(start, source.length);
        end = ByteArray.adjust(end, source.length);
        if (start < end) {
            index = ByteArray.adjustE(index, size);
            ByteArray.update(this, index, source, start, end);
        }
    }
    @Override
    public void update(int index, byte[] source, int start) {
        update(index, source, start, source.length);
    }
    @Override
    public void update(int index, byte[] source) {
        update(index, source, 0, source.length);
    }

    @Override
    public void update(int index, ByteArray source, int start, int end) {
        int srcLen = source.getSize();
        start = ByteArray.adjust(start, srcLen);
        end = ByteArray.adjust(end, srcLen);
        if (start < end) {
            index = ByteArray.adjustE(index, size);
            byte[] srcBuf = source.getBuffer();
            int srcOffset = source.getOffset();
            ByteArray.update(this, index, srcBuf, srcOffset + start, srcOffset + end);
        }
    }
    @Override
    public void update(int index, ByteArray source, int start) {
        update(index, source, start, source.getSize());
    }
    @Override
    public void update(int index, ByteArray source) {
        update(index, source, 0, source.getSize());
    }

    //
    //  Appending
    //

    @Override
    public void append(byte[] source, int start, int end) {
        start = ByteArray.adjust(start, source.length);
        end = ByteArray.adjust(end, source.length);
        if (start < end) {
            ByteArray.update(this, size, source, start, end);
        }
    }
    @Override
    public void append(byte[] source, int start) {
        append(source, start, source.length);
    }
    @Override
    public void append(byte[] source) {
        append(source, 0, source.length);
    }
    @Override
    public void append(byte[]... sources) {
        for (byte[] src : sources) {
            append(src, 0, src.length);
        }
    }

    @Override
    public void append(ByteArray source, int start, int end) {
        int srcLen = source.getSize();
        start = ByteArray.adjust(start, srcLen);
        end = ByteArray.adjust(end, srcLen);
        if (start < end) {
            byte[] srcBuf = source.getBuffer();
            int srcOffset = source.getOffset();
            ByteArray.update(this, size, srcBuf, srcOffset + start, srcOffset + end);
        }
    }
    @Override
    public void append(ByteArray source, int start) {
        append(source, start, source.getSize());
    }
    @Override
    public void append(ByteArray source) {
        append(source, 0, source.getSize());
    }
    @Override
    public void append(ByteArray... sources) {
        for (ByteArray src : sources) {
            append(src, 0, src.getSize());
        }
    }


    //
    //  Inserting
    //

    @Override
    public void insert(int index, byte[] source, int start, int end) {
        start = ByteArray.adjustE(start, source.length);
        end = ByteArray.adjustE(end, source.length);
        if (start < end) {
            index = ByteArray.adjustE(index, size);
            ByteArray.insert(this, index, source, start, end);
        }
    }
    @Override
    public void insert(int index, byte[] source, int start) {
        insert(index, source, start, source.length);
    }
    @Override
    public void insert(int index, byte[] source) {
        insert(index, source, 0, source.length);
    }

    @Override
    public void insert(int index, ByteArray source, int start, int end) {
        int srcLen = source.getSize();
        start = ByteArray.adjustE(start, srcLen);
        end = ByteArray.adjustE(end, srcLen);
        if (start < end) {
            index = ByteArray.adjustE(index, size);
            byte[] srcBuf = source.getBuffer();
            int srcOffset = source.getOffset();
            ByteArray.insert(this, index, srcBuf, srcOffset + start, srcOffset + end);
        }
    }
    @Override
    public void insert(int index, ByteArray source, int start) {
        insert(index, source, start, source.getSize());
    }
    @Override
    public void insert(int index, ByteArray source) {
        insert(index, source, 0, source.getSize());
    }

    /**
     *  Insert the value to this position
     *
     * @param index - position
     * @param value - byte value
     */
    @Override
    public void insert(int index, byte value) {
        index = ByteArray.adjustE(index, size);
        if (index < size) {
            ByteArray.insert(this, index, value);
        } else {
            // target position is out of range [offset, offset + size)
            // set it directly
            setByte(index, value);
        }
    }

    //
    //  Erasing
    //

    @Override
    public byte remove(int index) {
        index = ByteArray.adjustE(index, size);
        if (index >= size) {
            // too big
            throw new ArrayIndexOutOfBoundsException("index error: " + index + ", size: " + size);
        } else if (index == 0) {
            // remove the first element
            return shift();
        } else if (index == (size - 1)) {
            // remove the last element
            return pop();
        } else {
            return ByteArray.remove(this, index);
        }
    }

    @Override
    public byte shift() {
        if (size < 1) {
            throw new ArrayIndexOutOfBoundsException("data empty!");
        }
        byte erased = buffer[offset];
        ++offset;
        --size;
        return erased;
    }

    @Override
    public byte pop() {
        if (size < 1) {
            throw new ArrayIndexOutOfBoundsException("data empty!");
        }
        --size;
        return buffer[offset + size];
    }

    @Override
    public void push(byte element) {
        setByte(size, element);
    }
    @Override
    public void append(byte element) {
        setByte(size, element);
    }
    @Override
    public void append(char element) {
        setChar(size, element);
    }
}
