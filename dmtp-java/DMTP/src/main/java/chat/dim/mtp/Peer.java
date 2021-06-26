/* license: https://mit-license.org
 *
 *  MTP: Message Transfer Protocol
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
package chat.dim.mtp;

import java.lang.ref.WeakReference;
import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.List;

import chat.dim.mtp.task.Arrival;
import chat.dim.mtp.task.Assemble;
import chat.dim.mtp.task.Departure;
import chat.dim.network.DataConvert;
import chat.dim.type.MutableData;
import chat.dim.type.UInt32Data;

public class Peer extends Thread {

    private boolean running = false;

    private WeakReference<PeerDelegate> delegateRef = null;
    private WeakReference<PeerHandler> handlerRef = null;

    public final Pool pool;

    public Peer(Pool pool) {
        super();
        this.pool = pool;
    }

    public Peer() {
        this(new MemPool());
    }

    public synchronized PeerDelegate getDelegate() {
        if (delegateRef == null) {
            return null;
        }
        return delegateRef.get();
    }
    public synchronized void setDelegate(PeerDelegate delegate) {
        if (delegate == null) {
            delegateRef = null;
        } else {
            delegateRef = new WeakReference<>(delegate);
        }
    }

    public synchronized PeerHandler getHandler() {
        if (handlerRef == null) {
            return null;
        }
        return handlerRef.get();
    }
    public synchronized void setHandler(PeerHandler handler) {
        if (handler == null) {
            handlerRef = null;
        } else {
            handlerRef = new WeakReference<>(handler);
        }
    }

    @Override
    public void start() {
        if (isAlive()) {
            return;
        }
        running = true;
        super.start();
    }

    // stop()
    public void close() {
        running = false;
    }

    private void _sleep(double seconds) {
        try {
            sleep((long) (seconds * 1000));
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void run() {
        PeerHandler handler;
        int done;
        Departure departure;
        List<Assemble> assembling;
        while (running) {
            try {
                handler = getHandler();
                // first, process all arrivals
                done = cleanArrivals();
                // second, get one departure task
                departure = pool.shiftExpiredDeparture();
                if (departure == null) {
                    // third, if no departure task, remove expired fragments
                    assembling = pool.discardFragments();
                    for (Assemble item : assembling) {
                        handler.recycleFragments(item.getFragments(), item.source, item.destination);
                    }
                    if (done == 0) {
                        // all jobs done, have a rest. ^_^
                        _sleep(0.1);
                    }
                } else {
                    // redo this departure task
                    send(departure);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    /**
     *  Process the received packages in waiting list
     *
     * @return finished task count
     */
    private int cleanArrivals() {
        int done = 0;
        int total = pool.numberOfArrivals();
        Arrival arrival;
        while (done < total) {
            arrival = pool.shiftFirstArrival();
            if (arrival == null) {
                // no task now
                break;
            }
            handle(arrival);
            done += 1;
        }
        return done;
    }

    private void handle(Arrival task) {
        Package pack = Package.parse(task.payload);
        if (pack == null) {
            //throw new NullPointerException("package error: " + Arrays.toString(task.payload));
            getHandler().onReceivedError(task.payload, task.source, task.destination);
            return;
        }
        boolean ok;
        if (pack.isCommandResponse()) {
            // command response
            if (pool.deleteDeparture(pack, task.source, task.destination)) {
                // if departure task is deleted, means it's finished
                getHandler().onSendCommandSuccess(pack.head.sn, task.source, task.destination);
            }
            return;
        } else if (pack.isMessageResponse()) {
            // message response
            if (pool.deleteDeparture(pack, task.source, task.destination)) {
                // if departure task is deleted, means it's finished
                getHandler().onSendMessageSuccess(pack.head.sn, task.source, task.destination);
            }
            return;
        } else if (pack.isCommand()) {
            // handle command
            ok = getHandler().onReceivedCommand(pack.body, task.source, task.destination);
        } else if (pack.isMessage()) {
            // handle message
            ok = getHandler().onReceivedMessage(pack.body, task.source, task.destination);
        } else {
            // handle message fragment
            assert pack.isMessageFragment() : "data type error: " + pack.head.type;
            ok = getHandler().checkFragment(pack, task.source, task.destination);
            if (ok) {
                // assemble fragments
                Package msg = pool.insertFragment(pack, task.source, task.destination);
                if (msg != null) {
                    // all fragments received
                    getHandler().onReceivedMessage(msg.body, task.source, task.destination);
                }
            }
        }
        // respond to the sender
        if (ok) {
            respond(pack, task.source, task.destination);
        }
    }

    private void respond(Package pack, SocketAddress remote, SocketAddress local) {
        MutableData body;
        DataType type;
        if (pack.isCommand()) {
            type = DataType.CommandResponse;
            body = new MutableData(2);
            body.setChar(0, 'O');
            body.setChar(1, 'K');
        } else if (pack.isMessage()) {
            type = DataType.MessageResponse;
            body = new MutableData(2);
            body.setChar(0, 'O');
            body.setChar(1, 'K');
        } else if (pack.isMessageFragment()) {
            type = DataType.MessageResponse;
            UInt32Data pages = DataConvert.getUInt32Data(pack.head.pages);
            UInt32Data offset = DataConvert.getUInt32Data(pack.head.offset);
            body = new MutableData(10);
            body.append(pages);
            body.append(offset);
            body.append('O');
            body.append('K');
        } else {
            throw new IllegalArgumentException("data type error: " + pack.head.type);
        }
        Package response;
        if (pack.head.bodyLength < 0) {
            // UDP (unlimited)
            response = Package.create(type, pack.head.sn, 1, 0, -1, body);
        } else {
            // TCP
            response = Package.create(type, pack.head.sn, 1, 0, body.getSize(), body);
        }
        // send response directly, don't add this task to waiting list
        int res = getDelegate().sendData(response, remote, local);
        assert res == response.getSize() : "failed to respond: " + remote + ", " + type;
    }

    //
    //  Sending
    //

    private void send(Departure task) {
        if (pool.appendDeparture(task)) {
            // treat the task as a bundle of packages
            PeerDelegate delegate = getDelegate();
            int res;
            List<Package> packages = task.packages;
            for (Package item : packages) {
                res = delegate.sendData(item, task.destination, task.source);
                assert res == item.getSize() :
                        "failed to resend task (" + packages.size() + " packages) to: " + task.destination;
            }
        } else {
            // mission failed
            DataType type = task.type;
            if (type.isCommand()) {
                getHandler().onSendCommandTimeout(task.sn, task.destination, task.source);
            } else if (type.isMessage()) {
                getHandler().onSendMessageTimeout(task.sn, task.destination, task.source);
            } else {
                throw new IllegalArgumentException("data type error: " + type);
            }
        }
    }

    //
    //  Command
    //

    public Departure sendCommand(Package pack, SocketAddress destination, SocketAddress source) {
        // send command as single package
        List<Package> packages = new ArrayList<>();
        packages.add(pack);
        Departure task = new Departure(packages, destination, source);
        send(task);
        return task;
    }

    //
    //  Message
    //

    public Departure sendMessage(Package pack, SocketAddress destination, SocketAddress source) {
        List<Package> packages;
        if (pack.body.getSize() <= Packer.OPTIMAL_BODY_LENGTH || pack.head.type.equals(DataType.MessageFragment)) {
            packages = new ArrayList<>();
            packages.add(pack);
        } else {
            // split packages for large message
            packages = Packer.split(pack);
        }
        Departure task = new Departure(packages, destination, source);
        send(task);
        return task;
    }
}
