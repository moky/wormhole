/* license: https://mit-license.org
 *
 *  UDP: User Datagram Protocol
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
package chat.dim.net;

import java.io.IOException;
import java.net.SocketAddress;

import chat.dim.mtp.Package;

public abstract class PackageHub extends BaseHub {

    public PackageConnection getPackageConnection(SocketAddress remote, SocketAddress local) {
        Connection conn = connect(remote, local);
        if (conn instanceof PackageConnection) {
            return (PackageConnection) conn;
        } else {
            return null;
        }
    }

    public Package receivePackage(SocketAddress source, SocketAddress destination) {
        PackageConnection conn = getPackageConnection(source, destination);
        try {
            return conn == null ? null : conn.receivePackage(source, destination);
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    public boolean sendPackage(Package pack, SocketAddress source, SocketAddress destination) {
        PackageConnection conn = getPackageConnection(destination, source);
        try {
            conn.sendPackage(pack, source, destination);
            return true;
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
    }
}
