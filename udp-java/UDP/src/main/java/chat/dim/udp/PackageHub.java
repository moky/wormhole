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
package chat.dim.udp;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.util.Set;

import chat.dim.net.BaseHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.socket.Reader;
import chat.dim.socket.Writer;
import chat.dim.type.AddressPairMap;

class ChannelPool extends AddressPairMap<Channel> {

    @Override
    public void set(SocketAddress remote, SocketAddress local, Channel value) {
        Channel old = get(remote, local);
        if (old != null && old != value) {
            remove(remote, local, old);
        }
        super.set(remote, local, value);
    }

    @Override
    public Channel remove(SocketAddress remote, SocketAddress local, Channel value) {
        Channel cached = super.remove(remote, local, value);
        if (cached != null && cached.isOpen()) {
            try {
                cached.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return cached;
    }
}

public abstract class PackageHub extends BaseHub {

    // (null, local) => channel
    private final ChannelPool channelPool = new ChannelPool();

    protected PackageHub(Connection.Delegate delegate) {
        super(delegate);
    }

    public void bind(SocketAddress local) throws IOException {
        Channel sock = getChannel(local);
        if (sock == null) {
            DatagramChannel udp = DatagramChannel.open();
            udp.socket().bind(local);
            udp.configureBlocking(false);
            Channel channel = createChannel(udp, local);
            putChannel(channel);
        }
    }

    //
    //  Channel
    //

    /**
     *  Create channel with socket & address
     *
     * @param sock   - socket
     * @param local  - local address
     * @return null on socket error
     */
    protected Channel createChannel(DatagramChannel sock, SocketAddress local) {
        return new PackageChannel(sock, null, local) {

            @Override
            protected Reader createReader() {
                return new PackageChannelReader(this) {
                    @Override
                    protected IOException checkData(ByteBuffer buf, int len, DatagramChannel sock) {
                        // TODO: check 'E_AGAIN' & TimeoutException
                        return null;
                    }

                    @Override
                    protected IOException checkError(IOException error, DatagramChannel sock) {
                        // TODO: check TimeoutException
                        return error;
                    }
                };
            }

            @Override
            protected Writer createWriter() {
                return new PackageChannelWriter(this) {
                    @Override
                    protected IOException checkError(IOException error, DatagramChannel sock) {
                        // TODO: check 'E_AGAIN' & TimeoutException
                        return error;
                    }
                };
            }
        };
    }

    @Override
    protected Set<Channel> allChannels() {
        return channelPool.allValues();
    }

    protected Channel getChannel(SocketAddress local) {
        return channelPool.get(null, local);
    }

    protected void putChannel(Channel channel) {
        channelPool.set(channel.getRemoteAddress(), channel.getLocalAddress(), channel);
    }

    @Override
    protected void removeChannel(Channel channel) {
        channelPool.remove(channel.getRemoteAddress(), channel.getLocalAddress(), channel);
    }

    @Override
    public Channel open(SocketAddress remote, SocketAddress local) {
        if (local == null) {
            // get any channel
            Set<Channel> all = allChannels();
            SocketAddress address;
            for (Channel channel : all) {
                address = channel.getRemoteAddress();
                if (address == null || address.equals(remote)) {
                    return channel;
                }
            }
            // channel not found
            return null;
        }
        // get channel bound to local address
        return getChannel(local);
    }
}
