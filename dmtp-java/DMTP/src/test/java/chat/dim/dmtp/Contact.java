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

import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.dmtp.values.*;
import chat.dim.tlv.Data;
import chat.dim.udp.Connection;

public class Contact {

    public static long EXPIRES = 60 * 60 * 24; // 24 hours

    public final String identifier;

    // locations order by time
    private final List<LocationValue> locations = new ArrayList<>();
    private final ReadWriteLock locationLock = new ReentrantReadWriteLock();

    public Contact(String id) {
        super();
        this.identifier = id;
    }

    /**
     *  Check connection for client node; check timestamp for server node
     *
     * @param location - location info
     * @param peer     - node peer
     * @return true to remove it
     */
    protected boolean isExpired(LocationValue location, Peer peer) {
        if (peer == null) {
            TimestampValue timestamp = location.getTimestamp();
            if (timestamp == null) {
                return true;
            }
            long now = (new Date()).getTime() / 1000;
            return now > (timestamp.value + EXPIRES);
        }
        // check connections for client node
        SourceAddressValue sourceAddress = location.getSourceAddress();
        if (isConnecting(sourceAddress.ip, sourceAddress.port, peer)) {
            return false;
        }
        MappedAddressValue mappedAddress = location.getMappedAddress();
        if (isConnecting(mappedAddress.ip, mappedAddress.port, peer)) {
            return false;
        }
        return true;
    }

    private boolean isConnecting(String host, int port, Peer peer) {
        SocketAddress address = new InetSocketAddress(host, port);
        Connection conn = peer.getConnection(address);
        if (conn == null) {
            return false;
        }
        return !conn.isError();
    }

    public void purge(Peer peer) {
        Lock writeLock = locationLock.writeLock();
        writeLock.lock();
        try {
            LocationValue item;
            for (int index = locations.size() - 1; index >= 0; --index) {
                item = locations.get(index);
                if (isExpired(item, peer)) {
                    locations.remove(index);
                }
            }
        } finally {
            writeLock.unlock();
        }
    }

    public LocationValue anyLocation() {
        LocationValue location = null;
        Lock readLock = locationLock.readLock();
        readLock.lock();
        try {
            int index = locations.size() - 1;
            if (index >= 0) {
                location = locations.get(index);
            }
        } finally {
            readLock.unlock();
        }
        return location;
    }

    /**
     *  Get all locations
     *
     * @return locations ordered by time (reversed)
     */
    public List<LocationValue> allLocations() {
        List<LocationValue> reversed = new ArrayList<>();
        Lock readLock = locationLock.readLock();
        readLock.lock();
        try {
            LocationValue item;
            int index;
            for (index = locations.size() - 1; index >= 0; --index) {
                item = locations.get(index);
                reversed.add(item);
            }
        } finally {
            readLock.unlock();
        }
        return reversed;
    }

    public LocationValue getLocation(SocketAddress address) {
        LocationValue location = null;
        Lock readLock = locationLock.readLock();
        readLock.lock();
        try {
            assert address instanceof InetSocketAddress : "address error: " + address;
            String host = ((InetSocketAddress) address).getHostString();
            int port = ((InetSocketAddress) address).getPort();
            SourceAddressValue sourceAddress;
            MappedAddressValue mappedAddress;
            LocationValue item;
            int index;
            for (index = locations.size() - 1; index >= 0; --index) {
                item = locations.get(index);
                // check source address
                sourceAddress = item.getSourceAddress();
                if (port == sourceAddress.port && host.equals(sourceAddress.ip)) {
                    location = item;
                    break;
                }
                // check mapped address
                mappedAddress = item.getMappedAddress();
                if (port == mappedAddress.port && host.equals(mappedAddress.ip)) {
                    location = item;
                    break;
                }
            }
        } finally {
            readLock.unlock();
        }
        return location;
    }

    /**
     *  When received 'HI' command, update the location in it
     *
     * @param location - location info with signature and time
     * @return false on error
     */
    public boolean storeLocation(LocationValue location) {
        if (!verifyLocation(location)) {
            return false;
        }

        boolean ok = true;
        Lock writeLock = locationLock.writeLock();
        writeLock.lock();
        try {
            SourceAddressValue sourceAddress = location.getSourceAddress();
            MappedAddressValue mappedAddress = location.getMappedAddress();
            TimestampValue timestamp = location.getTimestamp();

            LocationValue item;
            int index;
            for (index = locations.size() - 1; index >= 0; --index) {
                item = locations.get(index);
                if (!sourceAddress.equals(item.getSourceAddress())) {
                    continue;
                }
                if (!mappedAddress.equals(item.getMappedAddress())) {
                    continue;
                }
                if (timestamp.value < item.getTimestamp().value) {
                    ok = false;
                    break;
                }
                // remove location(s) with same addresses
                locations.remove(index);
            }
            if (ok) {
                // insert (ordered by time)
                for (index = locations.size() - 1; index >= 0; --index) {
                    item = locations.get(index);
                    if (timestamp.value >= item.getTimestamp().value) {
                        // got the position
                        break;
                    }
                }
                // insert after it
                locations.add(index + 1, location);
            }
        } finally {
            writeLock.unlock();
        }
        return ok;
    }

    /**
     *  When receive 'BYE' command, remove the location in it
     *
     * @param location - location info with signature and time
     * @return false on error
     */
    public boolean clearLocation(LocationValue location) {
        if (!verifyLocation(location)) {
            return false;
        }

        int count = 0;
        Lock writeLock = locationLock.writeLock();
        writeLock.lock();
        try {
            SourceAddressValue sourceAddress = location.getSourceAddress();
            MappedAddressValue mappedAddress = location.getMappedAddress();

            LocationValue item;
            int index;
            for (index = locations.size() - 1; index >= 0; --index) {
                item = locations.get(index);
                if (!sourceAddress.equals(item.getSourceAddress())) {
                    continue;
                }
                if (!mappedAddress.equals(item.getMappedAddress())) {
                    continue;
                }
                // remove location(s) with same addresses
                locations.remove(index);
                ++count;
            }
        } finally {
            writeLock.unlock();
        }
        return count > 0;
    }

    //
    //  Sign
    //

    private static byte[] getSignData(LocationValue location) {
        SourceAddressValue sourceAddress = location.getSourceAddress();
        MappedAddressValue mappedAddress = location.getMappedAddress();
        RelayedAddressValue relayedAddress = location.getRelayedAddress();
        TimestampValue timestamp = location.getTimestamp();
        // data = "source_address" + "mapped_address" + "relayed_address" + "time"
        if (mappedAddress == null) {
            return null;
        }
        byte[] data = mappedAddress.data;
        if (sourceAddress != null) {
            data = Data.concat(sourceAddress.data, data);
        }
        if (relayedAddress != null) {
            data = Data.concat(data, relayedAddress.data);
        }
        if (timestamp != null) {
            data = Data.concat(data, timestamp.data);
        }
        return data;
    }

    private static byte[] getSignature(LocationValue location) {
        BinaryValue signature = location.getSignature();
        if (signature == null) {
            return null;
        }
        return signature.data;
    }

    /**
     *  Sign location addresses and time
     *
     * @param location - location info with 'MAPPED-ADDRESS' from server
     * @return signed location info
     */
    public LocationValue signLocation(LocationValue location) {
        byte[] data = getSignData(location);
        if (data == null) {
            return null;
        }
        // TODO: sign it with private key
        byte[] sign = ("sign(" + Arrays.toString(data) + ")").getBytes();
        BinaryValue signature = new BinaryValue(sign);
        // create
        return LocationValue.create(location.getIdentifier(),
                location.getSourceAddress(),
                location.getMappedAddress(),
                location.getRelayedAddress(),
                location.getTimestamp(),
                signature,
                location.getNat());
    }

    public boolean verifyLocation(LocationValue location) {
        StringValue identifier = location.getIdentifier();
        SourceAddressValue sourceAddress = location.getSourceAddress();
        TimestampValue timestamp = location.getTimestamp();
        if (identifier == null || sourceAddress == null || timestamp == null) {
            return false;
        }

        byte[] data = getSignData(location);
        byte[] signature = getSignature(location);
        if (data == null || signature == null) {
            return false;
        }
        // TODO: verify data and signature with public key
        return true;
    }
}
