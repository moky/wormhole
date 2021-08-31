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
import java.util.List;

import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.LocationValue;
import chat.dim.dmtp.protocol.Message;
import chat.dim.mtp.Header;
import chat.dim.mtp.Package;
import chat.dim.tlv.Field;
import chat.dim.type.ByteArray;

public abstract class Node {

    private WeakReference<LocationDelegate> delegateRef = null;

    public synchronized LocationDelegate getDelegate() {
        return delegateRef == null ? null : delegateRef.get();
    }
    public synchronized void setDelegate(LocationDelegate delegate) {
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }
    }

    protected abstract void connect(SocketAddress remote);

    //
    //  Send
    //

    public abstract boolean sendMessage(Message msg, SocketAddress destination);

    public abstract boolean sendCommand(Command cmd, SocketAddress destination);

    /**
     *  Send current user ID/location to destination
     *
     * @param destination - server address
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
        Command cmd = Command.createHelloCommand(mine);
        return sendCommand(cmd, destination);
    }

    //
    //  Receive
    //

    protected boolean onReceivedPackage(SocketAddress remote, Package pack) {
        Header head = pack.head;
        if (head.isMessage()) {
            return onReceivedMessage(pack.body, remote);
        } else if (head.isCommand()) {
            return onReceivedCommand(pack.body, remote);
        } else {
            throw new IllegalArgumentException("data type error: " + head.type);
        }
    }

    private boolean onReceivedMessage(ByteArray msg, SocketAddress source) {
        // process after received message data
        List<Field> fields = Field.parseFields(msg);
        Message pack = new Message(msg, fields);
        return processMessage(pack, source);
    }

    private boolean onReceivedCommand(ByteArray cmd, SocketAddress source) {
        boolean ok = false;
        // process after received command data
        List<Command> commands = Command.parseCommands(cmd);
        for (Command pack : commands) {
            if (processCommand(pack, source)) {
                ok = true;
            }
        }
        return ok;
    }

    //
    //  Process
    //

    protected abstract boolean processMessage(Message msg, SocketAddress source);

    protected boolean processCommand(Command cmd, SocketAddress source) {
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
     *  Respond current ID info
     *
     * @param source - remote address
     * @return false on error
     */
    protected boolean processWho(SocketAddress source) {
        // say hi when the sender asked "Who are you?"
        return sayHello(source);
    }

    /**
     *  Accept location info
     *
     * @param location - location info
     * @param source   - remote address
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
     * @param source   - remote address
     * @return false on error
     */
    protected boolean processBye(LocationValue location, SocketAddress source) {
        // check location signature and remove it
        LocationDelegate delegate = getDelegate();
        assert delegate != null : "location delegate not set yet";
        return delegate.clearLocation(location);
    }
}
