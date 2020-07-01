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

import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.net.SocketException;
import java.util.List;

import chat.dim.dmtp.fields.Field;
import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.Message;
import chat.dim.dmtp.values.LocationValue;
import chat.dim.mtp.PeerHandler;
import chat.dim.mtp.Pool;
import chat.dim.mtp.protocol.DataType;
import chat.dim.mtp.protocol.Package;
import chat.dim.mtp.protocol.TransactionID;
import chat.dim.mtp.task.Departure;

public abstract class Node implements PeerHandler {

    public final Peer peer;

    private WeakReference<LocationDelegate> delegateRef = null;

    public Node(Peer peer) {
        super();
        this.peer = peer;
        peer.setHandler(this);
    }

    public Node(SocketAddress address, Hub hub, Pool pool) {
        this(new Peer(address, hub, pool));
    }

    public Node(SocketAddress address, Hub hub) {
        this(new Peer(address, hub));
    }

    public Node(SocketAddress address, Pool pool) throws SocketException {
        this(new Peer(address, pool));
    }

    public Node(SocketAddress address) throws SocketException {
        this(new Peer(address));
    }

    public synchronized LocationDelegate getDelegate() {
        if (delegateRef == null) {
            return null;
        }
        return delegateRef.get();
    }
    public synchronized void setDelegate(LocationDelegate delegate) {
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }
    }

    public void start() {
        // start peer
        peer.start();
    }

    public void stop() {
        close();
    }

    public void close() {
        // stop peer
        peer.close();
    }

    //
    //  Send
    //

    /**
     *  Send command data to destination address
     *
     * @param cmd         - command data
     * @param destination - remote IP and port
     * @return departure task with 'trans_id' in the payload
     */
    public Departure sendCommand(byte[] cmd, SocketAddress destination) {
        Package pack = Package.create(DataType.Command, cmd);
        return peer.sendCommand(pack, destination);
    }

    /**
     *  Send message data to destination address
     *
     * @param msg         - message data
     * @param destination - remote IP and port
     * @return departure task with 'trans_id' in the payload
     */
    public Departure sendMessage(byte[] msg, SocketAddress destination) {
        Package pack = Package.create(DataType.Message, msg);
        return peer.sendMessage(pack, destination);
    }

    /**
     *  Send command to destination address
     *
     * @param cmd         -
     * @param destination - remote IP and port
     * @return departure task with 'trans_id' in the payload
     */
    public Departure sendCommand(Command cmd, SocketAddress destination) {
        return sendCommand(cmd.data, destination);
    }

    /**
     *  Send message to destination address
     *
     * @param msg         -
     * @param destination - remote address
     * @return departure task with 'trans_id' in the payload
     */
    public Departure sendMessage(Message msg, SocketAddress destination) {
        return sendMessage(msg.data, destination);
    }

    /**
     *  Send current user ID/location to destination
     *
     * @param destination - server IP and port
     * @return false on error
     */
    public boolean sayHello(SocketAddress destination) {
        LocationDelegate delegate = getDelegate();
        assert delegate != null : "location delegate not set yet";
        LocationValue mine = delegate.currentLocation();
        if (mine == null) {
            //throw new NullPointerException("failed to get my location");
            return false;
        }
        Command cmd = Command.Hello.create(mine);
        sendCommand(cmd, destination);
        return true;
    }

    //
    //  Process
    //

    protected boolean processWho(SocketAddress source) {
        // say hi when the sender asked "Who are you?"
        return sayHello(source);
    }

    /**
     *  Accept location info
     *
     * @param location - location info
     * @param source   - remote IP and port
     * @return false on error
     */
    protected boolean processHello(LocationValue location, SocketAddress source) {
        // check location signature and save it
        LocationDelegate delegate = getDelegate();
        assert delegate != null : "location delegate not set yet";
        return delegate.storeLocation(location);
    }

    /**
     *  Check location info; if signature matched, remove it.
     *
     * @param location - location info
     * @param source   - remote IP and port
     * @return false on error
     */
    protected boolean processBye(LocationValue location, SocketAddress source) {
        // check location signature and remove it
        LocationDelegate delegate = getDelegate();
        assert delegate != null : "location delegate not set yet";
        return delegate.clearLocation(location);
    }

    /**
     *  Process received command from remote source address
     *
     * @param cmd    - command info
     * @param source - remote IP and port
     * @return false on error
     */
    public boolean processCommand(Command cmd, SocketAddress source) {
        if (cmd.tag.equals(Command.WHO))
        {
            return processWho(source);
        }
        else if (cmd.tag.equals(Command.HELLO))
        {
            assert cmd.value instanceof LocationValue : "login cmd error: " + cmd.value;
            return processHello((LocationValue) cmd.value, source);
        }
        else if (cmd.tag.equals(Command.BYE))
        {
            assert cmd.value instanceof LocationValue : "logout cmd error: " + cmd.value;
            return processBye((LocationValue) cmd.value, source);
        }
        else
        {
            System.out.printf("%s> unknown command: %s\n", getClass(), cmd);
            return false;
        }
    }

    /**
     *  Process received message from remote source address
     *
     * @param msg    - message info
     * @param source - remote IP and port
     * @return false on error
     */
    public abstract boolean processMessage(Message msg, SocketAddress source);

    //
    //  PeerHandler
    //

    @Override
    public void onSendCommandSuccess(TransactionID sn, SocketAddress destination, SocketAddress source) {
        // TODO: process after success to send command
    }

    @Override
    public void onSendCommandTimeout(TransactionID sn, SocketAddress destination, SocketAddress source) {
        // TODO: process after failed to send command
    }

    @Override
    public void onSendMessageSuccess(TransactionID sn, SocketAddress destination, SocketAddress source) {
        // TODO: process after success to send message
    }

    @Override
    public void onSendMessageTimeout(TransactionID sn, SocketAddress destination, SocketAddress source) {
        // TODO: process after failed to send message
    }

    @Override
    public boolean onReceivedCommand(byte[] cmd, SocketAddress source, SocketAddress destination) {
        // process after received command data
        List<Command> commands = Command.parseCommands(cmd);
        for (Command pack : commands) {
            processCommand(pack, source);
        }
        return true;
    }

    @Override
    public boolean onReceivedMessage(byte[] msg, SocketAddress source, SocketAddress destination) {
        // process after received message data
        List<Field> fields = Field.parseFields(msg);
        Message pack = new Message(msg);
        pack.setFields(fields);
        return processMessage(pack, source);
    }

    @Override
    public boolean checkFragment(Package fragment, SocketAddress source, SocketAddress destination) {
        // TODO: process after received command fragment
        return true;
    }

    @Override
    public void recycleFragments(List<Package> fragments, SocketAddress source, SocketAddress destination) {
        // TODO: process after failed to send message as fragments
    }
}
