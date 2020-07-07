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
import java.util.List;

import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.values.CommandValue;
import chat.dim.dmtp.values.LocationValue;
import chat.dim.mtp.Pool;

public abstract class Server extends Node {

    public Server(Peer peer) {
        super(peer);
    }

    public Server(SocketAddress address, Hub hub, Pool pool) throws SocketException {
        super(address, hub, pool);
    }

    public Server(SocketAddress address, Hub hub) throws SocketException {
        super(address, hub);
    }

    public Server(SocketAddress address, Pool pool) throws SocketException {
        super(address, pool);
    }

    public Server(SocketAddress address) throws SocketException {
        super(address);
    }

    //
    //  Process
    //

    @Override
    protected boolean processHello(LocationValue location, SocketAddress source) {
        // check 'MAPPED-ADDRESS
        SocketAddress mappedAddress = location.getMappedAddress();
        if (source.equals(mappedAddress)) {
            if (super.processHello(location, source)) {
                // location info accepted, create a connection to the source
                peer.connect(source);
                return true;
            }
        }
        // respond 'SIGN' command with 'ID' and 'MAPPED-ADDRESS'
        String id = location.getIdentifier();
        Command cmd = Command.Sign.create(id, source, null);
        sendCommand(cmd, source);
        return true;
    }

    protected boolean processCall(String receiver, SocketAddress source) {
        if (receiver == null) {
            //throw new NullPointerException("receiver ID not found: " + receiver);
            return false;
        }
        LocationDelegate delegate = getDelegate();
        assert delegate != null : "contact delegate not set yet";
        Command cmd;
        // get sessions of receiver
        List<LocationValue> locations = delegate.getLocations(receiver);
        if (locations.size() == 0) {
            // receiver offline
            // respond an empty "FROM" command to the sender
            cmd = Command.From.create(receiver);
            sendCommand(cmd, source);
            return false;
        }
        // receiver online
        LocationValue senderLocation = delegate.getLocation(source);
        if (senderLocation == null) {
            // sender offline
            // ask sender to login again
            cmd = Command.Who.create();
            sendCommand(cmd, source);
            return false;
        }
        // sender online
        SocketAddress address;
        // send command for each address
        for (LocationValue loc : locations) {
            address = loc.getMappedAddress();
            if (address == null) {
                continue;
            }
            // send "FROM" command with sender's location info to the receiver
            cmd = Command.From.create(senderLocation);
            sendCommand(cmd, address);
            // respond "FROM" command with receiver's location info to sender
            cmd = Command.From.create(loc);
            sendCommand(cmd, source);
        }
        return true;
    }

    @Override
    public boolean processCommand(Command cmd, SocketAddress source) {
        if (cmd.tag.equals(Command.CALL))
        {
            assert cmd.value instanceof CommandValue : "call command error: " + cmd.value;
            return processCall(((CommandValue) cmd.value).getIdentifier(), source);
        }
        else
        {
            return super.processCommand(cmd, source);
        }
    }
}
