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
import java.nio.channels.DatagramChannel;
import java.util.Set;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.socket.BaseHub;
import chat.dim.type.AddressPairMap;

class ChannelPool extends AddressPairMap<Channel> {

    @Override
    public Channel get(SocketAddress remote, SocketAddress local) {
        assert remote != null || local != null : "both addresses are empty";
        // -- Step 1 --
        //    (remote, local)
        //        this step will get the channel connected to the remote address
        //        and bound to the local address at the same time;
        //    (null, local)
        //        this step will get a channel bound to the local address, and
        //        surely not connected;
        //    (remote, null)
        //        this step will get a channel connected to the remote address,
        //        no matter which local address to be bound;
        Channel channel = super.get(remote, local);
        if (channel != null) {
            return channel;
        } else if (remote == null) {
            // failed to get a channel bound to the local address
            return null;
        }
        // -- Step 2 --
        //    (remote, local)
        //        try to get a channel which bound to the local address, but
        //        not connected to any remote address;
        //    (null, local)
        //        this situation has already done at step 1;
        if (local != null) {
            // ignore the remote address
            channel = super.get(null, local);
            if (channel != null && channel.getRemoteAddress() == null) {
                // got a channel not connected yet
                return channel;
            }
        }
        // -- Step 3 --
        //    (remote, null)
        //        try to get a channel that bound to any local address, but
        //        not connected yet;
        Set<Channel> all = allValues();
        for (Channel item : all) {
            if (item.getRemoteAddress() == null) {
                return item;
            }
        }
        // not found
        return null;
    }

    @Override
    public Channel set(SocketAddress remote, SocketAddress local, Channel value) {
        // remove cached item
        Channel cached = super.remove(remote, local, value);
        /*/
        if (cached != null && cached != value) {
            cached.close();
        }
        /*/
        Channel old = super.set(remote, local, value);
        assert old != null : "should not happen";
        return cached;
    }

    /*/
    @Override
    public Channel remove(SocketAddress remote, SocketAddress local, Channel value) {
        Channel cached = super.remove(remote, local, value);
        if (cached != null && cached != value) {
            try {
                cached.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        if (value != null) {
            try {
                value.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return cached;
    }
    /*/

}

/**
 *  Base Datagram Hub
 *  ~~~~~~~~~~~~~~~~~
 */
public abstract class PacketHub extends BaseHub {

    private final AddressPairMap<Channel> channelPool;

    protected PacketHub(Connection.Delegate gate) {
        super(gate);
        channelPool = createChannelPool();
    }

    protected AddressPairMap<Channel> createChannelPool() {
        return new ChannelPool();
    }

    public void bind(SocketAddress local) throws IOException {
        Channel sock = getChannel(null, local);
        if (sock == null) {
            DatagramChannel udp = DatagramChannel.open();
            udp.configureBlocking(true);
            udp.socket().setReuseAddress(true);
            udp.socket().bind(local);
            udp.configureBlocking(false);
            Channel channel = createChannel(null, local);
            if (channel instanceof PacketChannel) {
                ((PacketChannel) channel).setSocketChannel(udp);
            }
            Channel cached = setChannel(null, local, channel);
            if (cached != null && cached != channel) {
                cached.close();
            }
        }
    }

    //
    //  Channel
    //

    /**
     *  Create channel with socket & address
     *
     * @param remote - remote address
     * @param local  - local address
     * @return null on socket error
     */
    protected Channel createChannel(SocketAddress remote, SocketAddress local) {
        return new PacketChannel(remote, local);
    }

    @Override
    protected Iterable<Channel> allChannels() {
        return channelPool.allValues();
    }

    protected Channel getChannel(SocketAddress remote, SocketAddress local) {
        return channelPool.get(remote, local);
    }

    protected Channel setChannel(SocketAddress remote, SocketAddress local, Channel channel) {
        return channelPool.set(remote, local, channel);
    }

    @Override
    protected Channel removeChannel(SocketAddress remote, SocketAddress local, Channel channel) {
        return channelPool.remove(remote, local, channel);
    }

    @Override
    public Channel open(SocketAddress remote, SocketAddress local) {
        assert remote != null || local != null : "both addresses are empty";
        // get channel with direction (remote, local)
        return getChannel(remote, local);
    }

}
