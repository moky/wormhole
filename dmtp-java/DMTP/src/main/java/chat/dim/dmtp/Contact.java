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
import java.util.List;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.dmtp.values.*;

public class Contact {

    public final String identifier;

    // locations order by time
    private final List<LocationValue> locations = new ArrayList<>();
    private final ReadWriteLock locationLock = new ReentrantReadWriteLock();

    public Contact(String id) {
        super();
        this.identifier = id;
    }

    /**
     *  Get all locations
     *
     * @return locations ordered by time
     */
    public List<LocationValue> allLocations() {
        List<LocationValue> copy = new ArrayList<>();
        Lock readLock = locationLock.readLock();
        readLock.lock();
        try {
            copy.addAll(locations);
        } finally {
            readLock.unlock();
        }
        return copy;
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
            for (LocationValue loc : locations) {
                sourceAddress = loc.getSourceAddress();
                if (sourceAddress != null &&
                        port == sourceAddress.port &&
                        host.equals(sourceAddress.ip)) {
                    location = loc;
                    break;
                }
                mappedAddress = loc.getMappedAddress();
                if (mappedAddress != null &&
                        port == mappedAddress.port &&
                        host.equals(mappedAddress.ip)) {
                    location = loc;
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
    public boolean updateLocation(LocationValue location) {
        StringValue identifier = location.getIdentifier();
        SourceAddressValue sourceAddress = location.getSourceAddress();
        MappedAddressValue mappedAddress = location.getMappedAddress();
        TimestampValue timestamp = location.getTimestamp();
        BinaryValue signature = location.getSignature();
        if (identifier == null ||
                sourceAddress == null || mappedAddress == null ||
                timestamp == null || signature == null) {
            return false;
        }
        boolean ok = true;
        Lock writeLock = locationLock.writeLock();
        writeLock.lock();
        try {
            LocationValue loc;
            int pos;
            for (pos = locations.size() - 1; pos >= 0; --pos) {
                loc = locations.get(pos);
                if (!sourceAddress.equals(loc.getSourceAddress())) {
                    continue;
                }
                if (!mappedAddress.equals(loc.getMappedAddress())) {
                    continue;
                }
                if (timestamp.value < loc.getTimestamp().value) {
                    ok = false;
                    break;
                }
                // remove location(s) with same addresses
                locations.remove(pos);
            }
            if (ok) {
                // insert (ordered by time)
                for (pos = locations.size() - 1; pos >= 0; --pos) {
                    loc = locations.get(pos);
                    if (timestamp.value >= loc.getTimestamp().value) {
                        // insert after it
                        pos += 1;
                        break;
                    }
                }
                locations.add(pos, location);
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
    public boolean removeLocation(LocationValue location) {
        StringValue identifier = location.getIdentifier();
        SourceAddressValue sourceAddress = location.getSourceAddress();
        MappedAddressValue mappedAddress = location.getMappedAddress();
        TimestampValue timestamp = location.getTimestamp();
        BinaryValue signature = location.getSignature();
        if (identifier == null ||
                sourceAddress == null || mappedAddress == null ||
                timestamp == null || signature == null) {
            return false;
        }
        int count = 0;
        Lock writeLock = locationLock.writeLock();
        writeLock.lock();
        try {
            LocationValue loc;
            int pos;
            for (pos = locations.size() - 1; pos >= 0; --pos) {
                loc = locations.get(pos);
                if (!sourceAddress.equals(loc.getSourceAddress())) {
                    continue;
                }
                if (!mappedAddress.equals(loc.getMappedAddress())) {
                    continue;
                }
                // remove location(s) with same addresses
                locations.remove(pos);
                count += 1;
            }
        } finally {
            writeLock.unlock();
        }
        return count > 0;
    }
}
