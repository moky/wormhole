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
}
