/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
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
package chat.dim.type;

import java.io.Serializable;
import java.net.SocketAddress;
import java.util.Objects;

public class AddressPairObject implements Serializable {

    protected SocketAddress remoteAddress;
    protected SocketAddress localAddress;

    public AddressPairObject(SocketAddress remote, SocketAddress local) {
        remoteAddress = remote;
        localAddress = local;
    }

    public SocketAddress getLocalAddress() {
        return localAddress;
    }

    public SocketAddress getRemoteAddress() {
        return remoteAddress;
    }

    @Override
    public java.lang.String toString() {
        return "<" + getClass().getName() + ": remote=" + getRemoteAddress() + ", local=" + getLocalAddress() + " />";
    }

    @Override
    public int hashCode() {
        // name's hashCode is multiplied by an arbitrary prime number (13)
        // in order to make sure there is a difference in the hashCode between
        // these two parameters:
        //  name: a  value: aa
        //  name: aa value: a
        SocketAddress remote = remoteAddress;
        SocketAddress local = localAddress;
        if (remote == null) {
            return local == null ? 0 : local.hashCode();
        } else if (local == null) {
            return remote.hashCode() * 13;
        } else {
            return remote.hashCode() * 13 + local.hashCode();
        }
    }

    @Override
    public boolean equals(Object o) {
        if (o == null) {
            return remoteAddress == null && localAddress == null;
        } else if (o == this) {
            return true;
        } else if (o instanceof AddressPairObject) {
            AddressPairObject pair = (AddressPairObject) o;
            return Objects.equals(remoteAddress, pair.remoteAddress) &&
                    Objects.equals(localAddress, pair.localAddress);
        } else {
            return false;
        }
    }
}
