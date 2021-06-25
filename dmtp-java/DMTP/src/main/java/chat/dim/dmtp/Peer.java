/* license: https://mit-license.org
 *
 *  DMTP: Direct Message Transfer Protocol
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
package chat.dim.dmtp;

import java.net.SocketAddress;
import java.net.SocketException;
import java.util.Set;

import chat.dim.mtp.Package;
import chat.dim.mtp.Pool;
import chat.dim.mtp.task.Arrival;
import chat.dim.mtp.task.Departure;
import chat.dim.type.Data;
import chat.dim.udp.Connection;
import chat.dim.udp.ConnectionStatus;
import chat.dim.udp.HubFilter;
import chat.dim.udp.HubListener;

public class Peer extends chat.dim.mtp.Peer implements HubListener {

    public final SocketAddress localAddress;
    public final Hub hub;

    public Peer(SocketAddress address, Hub hub, Pool pool) {
        super(pool);
        this.localAddress = address;
        this.hub = hub;
        this.setDelegate(hub);
        hub.addListener(this);
    }

    public Peer(SocketAddress address, Hub hub) {
        super();
        this.localAddress = address;
        this.hub = hub;
        this.setDelegate(hub);
        hub.addListener(this);
    }

    public Peer(SocketAddress address, Pool pool) throws SocketException {
        this(address, createHub(address), pool);
    }

    public Peer(SocketAddress address) throws SocketException {
        this(address, createHub(address));
    }

    private static Hub createHub(SocketAddress localAddress) throws SocketException {
        Hub hub = new Hub();
        hub.open(localAddress);
        //hub.start();
        return hub;
    }

    @Override
    public void start() {
        // start peer
        super.start();
        // start hub
        hub.start();
    }

    @Override
    public void close() {
        // stop hub
        hub.close();
        // stop peer
        super.close();
    }

    //
    //  Connections
    //

    public Connection connect(SocketAddress remoteAddress) {
        return hub.connect(remoteAddress, localAddress);
    }

    public Set<Connection> disconnect(SocketAddress remoteAddress) {
        return hub.disconnect(remoteAddress, localAddress);
    }

    public Connection getConnection(SocketAddress remoteAddress) {
        return hub.getConnection(remoteAddress, localAddress);
    }

    //
    //  Send
    //

    public Departure sendCommand(Package pack, SocketAddress destination) {
        return sendCommand(pack, destination, localAddress);
    }

    public Departure sendMessage(Package pack, SocketAddress destination) {
        return sendMessage(pack, destination, localAddress);
    }

    //
    //  HubListener
    //

    @Override
    public HubFilter getFilter() {
        // TODO: create filter for connection
        return null;
    }

    @Override
    public byte[] onDataReceived(byte[] bytes, SocketAddress source, SocketAddress destination) {
        Arrival task = new Arrival(new Data(bytes), source, destination);
        pool.appendArrival(task);
        return null;
    }

    @Override
    public void onStatusChanged(Connection connection, ConnectionStatus oldStatus, ConnectionStatus newStatus) {
        // TODO: update for connection status
    }
}
