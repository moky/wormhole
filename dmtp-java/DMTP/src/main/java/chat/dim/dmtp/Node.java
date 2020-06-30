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

public class Node implements PeerHandler {

    public final Peer peer;

    private WeakReference<ContactDelegate> delegateRef = null;

    public Node(Peer peer) {
        super();
        this.peer = peer;
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

    public synchronized ContactDelegate getDelegate() {
        if (delegateRef == null) {
            return null;
        }
        return delegateRef.get();
    }
    public synchronized void setDelegate(ContactDelegate delegate) {
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
        peer.close();
    }

    //
    //  Send
    //

    /**
     *  Send command to destination address
     *
     * @param cmd         -
     * @param destination - remote IP and port
     * @return departure task with 'trans_id' in the payload
     */
    public Departure sendCommand(Command cmd, SocketAddress destination) {
        Package pack = Package.create(DataType.Command, cmd.data);
        return peer.sendCommand(pack, destination);
    }

    /**
     *  Send message to destination address
     *
     * @param msg         -
     * @param destination - remote address
     * @return departure task with 'trans_id' in the payload
     */
    public Departure sendMessage(Message msg, SocketAddress destination) {
        Package pack = Package.create(DataType.Message, msg.data);
        return peer.sendCommand(pack, destination);
    }

    //
    //  Process
    //

    public boolean sayHello(SocketAddress destination) {
        ContactDelegate delegate = getDelegate();
        assert delegate != null : "contact delegate not set yet";
        LocationValue mine = delegate.currentLocation();
        if (mine == null) {
            //throw new NullPointerException("failed to get my location");
            return false;
        }
        Command cmd = Command.Hello.create(mine);
        sendCommand(cmd, destination);
        return true;
    }

    protected boolean processWho(SocketAddress source) {
        // say hi when the sender asked "Who are you?"
        return sayHello(source);
    }

    protected boolean processHello(LocationValue location, SocketAddress source) {
        // TODO: check source address with location
        ContactDelegate delegate = getDelegate();
        assert delegate != null : "contact delegate not set yet";
        return delegate.updateLocation(location);
    }

    protected boolean processBye(LocationValue location, SocketAddress source) {
        // TODO: check source address with location
        ContactDelegate delegate = getDelegate();
        assert delegate != null : "contact delegate not set yet";
        return delegate.removeLocation(location);
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
            System.out.printf("%s> unknown command: %s", getClass(), cmd);
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
    public boolean processMessage(Message msg, SocketAddress source) {
        // TODO: implement me!
        return true;
    }

    //
    //  PeerHandler
    //

    @Override
    public void onSendCommandSuccess(TransactionID sn, SocketAddress destination, SocketAddress source) {

    }

    @Override
    public void onSendCommandTimeout(TransactionID sn, SocketAddress destination, SocketAddress source) {

    }

    @Override
    public void onSendMessageSuccess(TransactionID sn, SocketAddress destination, SocketAddress source) {

    }

    @Override
    public void onSendMessageTimeout(TransactionID sn, SocketAddress destination, SocketAddress source) {

    }

    @Override
    public boolean onReceivedCommand(byte[] cmd, SocketAddress source, SocketAddress destination) {
        List<Field> commands = Command.parseFields(cmd);
        for (Field pack : commands) {
            assert pack instanceof Command : "command error: " + pack;
            processCommand((Command) pack, source);
        }
        return true;
    }

    @Override
    public boolean onReceivedMessage(byte[] msg, SocketAddress source, SocketAddress destination) {
        List<Field> fields = Field.parseFields(msg);
        Message pack = new Message(msg, fields);
        return processMessage(pack, source);
    }

    @Override
    public boolean checkFragment(Package fragment, SocketAddress source, SocketAddress destination) {
        // TODO: check fragment
        return true;
    }

    @Override
    public void recycleFragments(List<Package> fragments, SocketAddress source, SocketAddress destination) {

    }
}
