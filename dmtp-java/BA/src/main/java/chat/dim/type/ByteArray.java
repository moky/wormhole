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
    // get data offset
    int getOffset();
    // get data length
    int getLength();

    String toHexString();

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
}
