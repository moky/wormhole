/* license: https://mit-license.org
 *
 *  MTP: Message Transfer Protocol
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
package chat.dim.mtp;

import java.io.IOException;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.util.List;

import chat.dim.net.BaseConnection;
import chat.dim.net.Channel;
import chat.dim.type.ByteArray;
import chat.dim.type.Data;

public class PackageConnection extends BaseConnection<Package> {

    private final ArrivalHall arrivalHall = new ArrivalHall();
    private final DepartureHall departureHall = new DepartureHall();

    public PackageConnection(Channel byteChannel, SocketAddress remote, SocketAddress local) {
        super(byteChannel, remote, local);
    }

    @Override
    public void tick() {
        super.tick();
        try {
            processExpiredTasks();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /**
     *  Append the package into a waiting queue for sending out
     *
     * @param body        - message body
     * @param destination - remote address
     * @throws IOException on error
     */
    public void sendCommand(byte[] body, SocketAddress destination) throws IOException {
        Package pack = Package.create(DataType.COMMAND, new Data(body));
        send(pack, destination);
    }
    public void sendMessage(byte[] body, SocketAddress destination) throws IOException {
        Package pack = Package.create(DataType.MESSAGE, new Data(body));
        send(pack, destination);
    }

    @Override
    public int send(Package pack, SocketAddress destination) throws IOException {
        // append as Departure task to waiting queue
        departureHall.appendDeparture(pack, getLocalAddress(), destination);
        // send out tasks from waiting queue
        processExpiredTasks();
        return 0;
    }

    private void processExpiredTasks() throws IOException {
        // check departures
        Departure outgo;
        while (true) {
            outgo = departureHall.getNextExpiredDeparture();
            if (outgo == null) {
                // all job done
                break;
            } else if (!sendDeparture(outgo)) {
                // task error
                departureHall.removeDeparture(outgo);
            }
        }
        // check arrivals
        arrivalHall.clearExpiredArrivals();
    }

    private boolean sendDeparture(Departure task) throws IOException {
        // get fragments
        List<Package> fragments = task.getFragments();
        if (fragments == null || fragments.size() == 0) {
            // all fragments respond?
            return false;
        }
        // send out all fragments
        byte[] data;
        ByteBuffer buffer = null;
        for (Package pack : fragments) {
            // get buffer for data pack
            data = pack.getBytes();
            if (buffer == null || buffer.capacity() < data.length) {
                buffer = ByteBuffer.allocate(data.length);
            } else {
                buffer.clear();
            }
            buffer.put(data);
            buffer.flip();
            send(buffer, task.destination);
        }
        return true;
    }

    private void respondCommand(TransactionID sn, byte[] body, SocketAddress remote) {
        Package res = Package.create(DataType.COMMAND_RESPONSE, sn, new Data(body));
        try {
            send(res, remote);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    private void respondMessage(TransactionID sn, int pages, int index, SocketAddress remote) {
        Package res = Package.create(DataType.MESSAGE_RESPONSE, sn, pages, index, new Data(OK));
        try {
            send(res, remote);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected Package parse(byte[] data, SocketAddress remote) {
        // process income package
        Package pack = Package.parse(new Data(data));
        if (pack == null) {
            return null;
        }
        ByteArray body = pack.body;
        if (body == null || body.getSize() == 0) {
            // should not happen
            return null;
        }
        // check data type in package header
        Header head = pack.head;
        DataType type = head.type;

        if (type.isCommandResponse()) {
            // process CommandResponse:
            //      'PONG'
            //      'OK'
            assert head.index == 0 : "command index error: " + head.index;
            departureHall.deleteFragment(head.sn, head.index);
            if (body.equals(PONG) || body.equals(OK)) {
                // ignore
                return null;
            }
            // Unknown Command Response?
            // let the caller to process it
        } else if (type.isCommand()) {
            // process Command:
            //      'PING'
            //      '...'
            if (body.equals(PING)) {
                // PING -> PONG
                respondCommand(head.sn, PONG, remote);
                return null;
            }
            respondCommand(head.sn, OK, remote);
            // Unknown Command?
            // let the caller to process it
        } else if (type.isMessageResponse()) {
            // process MessageResponse:
            //      'OK'
            //      'AGAIN'
            if (body.equals(AGAIN)) {
                // TODO: reset maxRetries?
                return null;
            }
            departureHall.deleteFragment(head.sn, head.index);
            if (body.equals(OK)) {
                // ignore
                return null;
            }
            // Unknown Message Response?
            // let the caller to process it
        } else {
            // process Message/Fragment:
            //      '...'
            respondMessage(head.sn, head.pages, head.index, remote);
            if (type.isFragment()) {
                // check cached fragments
                pack = arrivalHall.insertFragment(pack, remote, getLocalAddress());
            }
            // let the caller to process the message
        }

        if (body.equals(NOOP)) {
            // do nothing
            return null;
        }
        if (body.equals(PING) || body.equals(PONG)) {
            // FIXME: these bodies should be in a Command
            // ignore them
            return null;
        }
        return pack;
    }

    protected static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
}
