/* license: https://mit-license.org
 *
 *  Star Gate: Interfaces for network connection
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
package chat.dim.startrek;

import chat.dim.mtp.protocol.DataType;
import chat.dim.mtp.protocol.Header;
import chat.dim.mtp.protocol.Package;
import chat.dim.stargate.Gate;
import chat.dim.stargate.Ship;
import chat.dim.stargate.StarDocker;
import chat.dim.stargate.StarGate;
import chat.dim.stargate.StarShip;
import chat.dim.tcp.Connection;
import chat.dim.tlv.Data;

/**
 *  Star Docker for MTP packages
 */
public class MTPDocker extends StarDocker {

    public MTPDocker(StarGate gate) {
        super(gate);
    }

    public static boolean check(Connection connection) {
        byte[] buffer = connection.received();
        if (buffer == null) {
            return false;
        } else {
            return Header.parse(new Data(buffer)) != null;
        }
    }

    @Override
    public StarShip pack(byte[] payload, int priority, Ship.Delegate delegate) {
        Data req = new Data(payload);
        Package mtp = Package.create(DataType.Message, req.getLength(), req);
        return new MTPShip(mtp, priority, delegate);
    }

    private Package receivePackage() {
        // 1. check received data
        byte[] buffer = getGate().received();
        if (buffer == null) {
            // received nothing
            return null;
        }
        Data data = new Data(buffer);
        Header head = Header.parse(data);
        if (head == null) {
            // not a MTP package?
            if (buffer.length < 20) {
                // wait for more data
                return null;
            }
            int pos = data.find(Header.MAGIC_CODE, 1);
            if (pos > 0) {
                // found next head(starts with 'DIM'), skip data before it
                getGate().receive(pos);
            } else {
                // skip thw whole data
                getGate().receive(buffer.length);
            }
            return null;
        }
        // 2. receive data with 'head.length + body.length'
        int bodyLen = head.bodyLength;
        if (bodyLen < 0) {
            // should not happen
            bodyLen = buffer.length - head.getLength();
        }
        int packLen = head.getLength() + bodyLen;
        if (packLen > buffer.length) {
            // waiting for more data
            return null;
        }
        // receive package
        buffer = getGate().receive(packLen);
        data = new Data(buffer);
        Data body = data.slice(head.getLength());
        return new Package(data, head, body);
    }

    @Override
    protected Ship getIncomeShip() {
        Package income = receivePackage();
        if (income == null) {
            return null;
        } else {
            return new MTPShip(income);
        }
    }

    @Override
    protected StarShip processIncomeShip(Ship income) {
        MTPShip ship = (MTPShip) income;
        Package mtp = ship.mtp;
        Header head = mtp.head;
        Data body = mtp.body;
        DataType type = head.type;
        // 1. check data type
        if (type.equals(DataType.Command)) {
            // respond for Command directly
            if (body.equals(PING)) {        // 'PING'
                Data res = new Data(PONG);  // 'PONG'
                mtp = Package.create(DataType.CommandRespond, head.sn, PONG.length, res);
                return new MTPShip(mtp, StarShip.SLOWER);
            }
            return null;
        } else if (type.equals(DataType.CommandRespond)) {
            // remove linked outgo Ship
            return super.processIncomeShip(income);
        } else if (type.equals(DataType.MessageFragment)) {
            // just ignore
            return null;
        } else if (type.equals(DataType.MessageRespond)) {
            // remove linked outgo Ship
            super.processIncomeShip(income);
            if (body.getLength() == 0 || body.equals(OK)) {
                // just ignore
                return null;
            } else if (body.equals(AGAIN)) {
                // TODO: mission failed, send the message again
                return null;
            }
        }
        // 2. process payload by delegate
        byte[] res = null;
        Gate.Delegate delegate = getGate().getDelegate();
        if (body.getLength() > 0 && delegate != null) {
            res = delegate.onReceived(getGate(), income);
        }
        // 3. response
        if (type.equals(DataType.Message)) {
            // respond for message
            if (res == null || res.length == 0) {
                res = OK;
            }
            mtp = Package.create(DataType.MessageRespond, head.sn, res.length, new Data(res));
            // send it directly
            getGate().send(mtp.getBytes());
        } else if (res != null && res.length > 0) {
            // push as new Message
            return pack(res, StarShip.SLOWER, null);
        }
        return null;
    }

    @Override
    protected boolean sendOutgoShip(StarShip outgo) {
        MTPShip ship = (MTPShip) outgo;
        // check data type
        if (outgo.getRetries() == 0 && ship.mtp.head.type.equals(DataType.Message)) {
            // put back for response
            getGate().parkShip(outgo);
        }
        // send out request data
        return super.sendOutgoShip(outgo);
    }

    @Override
    protected StarShip getHeartbeat() {
        Package pack = Package.create(DataType.Command, PING.length, new Data(PING));
        return new MTPShip(pack, StarShip.SLOWER);
    }

    private static final byte[] PING = {'P', 'I', 'N', 'G'};
    private static final byte[] PONG = {'P', 'O', 'N', 'G'};
    private static final byte[] AGAIN = {'A', 'G', 'A', 'I', 'N'};
    private static final byte[] OK = {'O', 'K'};
}
