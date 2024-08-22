/* license: https://mit-license.org
 *
 *  Star Trek: Interstellar Transport
 *
 *                                Written in 2024 by Moky <albert.moky@gmail.com>
 *
 * ==============================================================================
 * The MIT License (MIT)
 *
 * Copyright (c) 2024 Albert Moky
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
import java.nio.channels.DatagramChannel;
import java.nio.channels.NetworkChannel;
import java.nio.channels.SelectableChannel;
import java.nio.channels.SocketChannel;

public interface SocketHelper {

    static SocketAddress socketGetLocalAddress(SelectableChannel sock) {
        try {
            if (sock instanceof SocketChannel) {
                // TCP
                return ((SocketChannel) sock).getLocalAddress();
            } else if (sock instanceof DatagramChannel) {
                // UDP
                return ((DatagramChannel) sock).getLocalAddress();
            } else {
                assert false : "unknown socket channel: " + sock;
            }
        } catch (IOException ex) {
            ex.printStackTrace();
        }
        return null;
    }

    static SocketAddress socketGetRemoteAddress(SelectableChannel sock) {
        try {
            if (sock instanceof SocketChannel) {
                // TCP
                return ((SocketChannel) sock).getRemoteAddress();
            } else if (sock instanceof DatagramChannel) {
                // UDP
                return ((DatagramChannel) sock).getRemoteAddress();
            } else {
                assert false : "unknown socket channel: " + sock;
            }
        } catch (IOException ex) {
            ex.printStackTrace();
        }
        return null;
    }

    //
    //  Flags
    //

    static boolean socketIsBlocking(SelectableChannel sock) {
        return sock.isBlocking();
    }

    static boolean socketIsConnected(SelectableChannel sock) {
        if (sock instanceof SocketChannel) {
            // TCP
            return ((SocketChannel) sock).isConnected();
        } else if (sock instanceof DatagramChannel) {
            // UDP
            return ((DatagramChannel) sock).isConnected();
        } else {
            assert false : "unknown socket channel: " + sock;
            return false;
        }
    }

    static boolean socketIsBound(SelectableChannel sock) {
        if (sock instanceof SocketChannel) {
            // TCP
            return ((SocketChannel) sock).socket().isBound();
        } else if (sock instanceof DatagramChannel) {
            // UDP
            return ((DatagramChannel) sock).socket().isBound();
        } else {
            assert false : "unknown socket channel: " + sock;
            return false;
        }
    }

    static boolean socketIsOpen(SelectableChannel sock) {
        return sock.isOpen();
    }

    /**
     *  Ready for reading
     */
    static boolean socketIsAvailable(SelectableChannel sock) {
        assert sock != null : "socket channel empty";
        // TODO: check reading buffer
        return true;
    }

    /**
     *  Ready for writing
     */
    static boolean socketIsVacant(SelectableChannel sock) {
        assert sock != null : "socket channel empty";
        // TODO: check writing buffer
        return true;
    }


    //
    //  Async Socket I/O
    //

    static boolean socketBind(NetworkChannel sock, SocketAddress local) {
        try {
            sock.bind(local);
            return sock instanceof SelectableChannel && socketIsBound((SelectableChannel) sock);
        } catch (IOException e) {
            e.printStackTrace();
        }
        return false;
    }

    static boolean socketConnect(NetworkChannel sock, SocketAddress remote) {
        try {
            if (sock instanceof SocketChannel) {
                // TCP
                SocketChannel tcp = (SocketChannel) sock;
                return tcp.connect(remote);
            } else if (sock instanceof DatagramChannel) {
                // UDP
                DatagramChannel udp = (DatagramChannel) sock;
                udp.connect(remote);
                return udp.isConnected();
            } else {
                assert false : "unknown socket channel: " + sock;
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return false;
    }

    static boolean socketDisconnect(SelectableChannel sock) {
        try {
            if (sock instanceof SocketChannel) {
                // TCP
                SocketChannel tcp = (SocketChannel) sock;
                if (tcp.isOpen()) {
                    tcp.close();
                    return !tcp.isOpen();
                } else {
                    // already closed
                    return true;
                }
            } else if (sock instanceof DatagramChannel) {
                // UDP
                DatagramChannel udp = (DatagramChannel) sock;
                if (udp.isConnected()) {
                    udp.disconnect();
                }
                return !udp.isConnected();
            } else {
                assert false : "unknown socket channel: " + sock;
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return false;
    }

}
