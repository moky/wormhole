/* license: https://mit-license.org
 *
 *  Star Gate: Interfaces for network connection
 *
 *                                Written in 2021 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Albert Moky
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
package chat.dim.network;

import chat.dim.mtp.protocol.Package;
import chat.dim.stargate.StarShip;

/**
 *  Star Ship with MTP Package
 */
public class MTPShip extends StarShip {

    public final Package mtp;

    public MTPShip(Package pack, int prior, Delegate delegate) {
        super(prior, delegate);
        mtp = pack;
    }
    public MTPShip(Package pack, int prior) {
        this(pack, prior, null);
    }
    public MTPShip(Package pack) {
        this(pack, StarShip.NORMAL, null);
    }

    @Override
    public byte[] getPackage() {
        return mtp.getBytes();
    }

    @Override
    public byte[] getSN() {
        return mtp.head.sn.getBytes();
    }

    @Override
    public byte[] getPayload() {
        return mtp.body.getBytes();
    }
}
