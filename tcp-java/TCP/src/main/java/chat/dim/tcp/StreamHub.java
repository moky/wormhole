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

import java.io.IOException;
import java.net.SocketAddress;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import chat.dim.net.BaseHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;

public abstract class StreamHub extends BaseHub {

    // remote => channel
    private final Map<SocketAddress, Channel> channels = new HashMap<>();

    protected StreamHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Set<Channel> allChannels() {
        return new HashSet<>(channels.values());
    }

    protected void putChannel(Channel channel) {
        SocketAddress remote = channel.getRemoteAddress();
        channels.put(remote, channel);
    }

    @Override
    public Channel openChannel(SocketAddress remote, SocketAddress local) {
        assert remote != null : "remote address empty";
        return channels.get(remote);
    }

    @Override
    public void closeChannel(Channel channel) {
        if (channel == null) {
            return;
        } else {
            removeChannel(channel);
        }
        try {
            if (channel.isOpen()) {
                channel.close();
            }
        } catch (IOException e) {
            //e.printStackTrace();
        }
    }

    private void removeChannel(Channel channel) {
        SocketAddress remote = channel.getRemoteAddress();
        if (channels.remove(remote) == channel) {
            // removed by key
            return;
        }
        // remove by value
        Iterator<Map.Entry<SocketAddress, Channel>> it;
        it = channels.entrySet().iterator();
        while (it.hasNext()) {
            if (it.next().getValue() == channel) {
                it.remove();
            }
        }
    }
}
