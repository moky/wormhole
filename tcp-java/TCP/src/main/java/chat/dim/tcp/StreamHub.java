/* license: https://mit-license.org
 *
 *  TCP: Transmission Control Protocol
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
package chat.dim.tcp;

import java.net.SocketAddress;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.socket.BaseHub;
import chat.dim.type.AddressPairMap;

class ChannelPool extends AddressPairMap<Channel> {

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
 *  Base Stream Hub
 *  ~~~~~~~~~~~~~~~
 */
public abstract class StreamHub extends BaseHub {

    private final AddressPairMap<Channel> channelPool;

    protected StreamHub(Connection.Delegate gate) {
        super(gate);
        channelPool = createChannelPool();
    }

    protected AddressPairMap<Channel> createChannelPool() {
        return new ChannelPool();
    }

    //
    //  Channel
    //

    /**
     *  Create channel with socket & addresses
     *
     * @param remote - remote address
     * @param local  - local address
     * @return null on socket error
     */
    protected Channel createChannel(SocketAddress remote, SocketAddress local) {
        return new StreamChannel(remote, local);
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

}
