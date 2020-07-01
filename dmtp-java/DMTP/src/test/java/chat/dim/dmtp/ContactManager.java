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
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

import chat.dim.dmtp.values.*;

public class ContactManager implements LocationDelegate {

    public String identifier = null;

    private final SocketAddress sourceAddress;
    public String nat = "Unknown";

    private final Peer peer;

    // contacts
    private final Map<String, Contact> contacts = new HashMap<>();
    private final ReadWriteLock contactLock = new ReentrantReadWriteLock();

    // locations
    private final Map<SocketAddress, WeakReference<LocationValue>> locations = new HashMap<>();

    public ContactManager(Peer peer) {
        super();
        this.peer = peer;
        this.sourceAddress = peer.localAddress;
    }

    /**
     *  Create contact with user ID
     *
     * @param identifier - user ID
     * @return contact
     */
    protected Contact createContact(String identifier) {
        return new Contact(identifier);
    }

    private Contact getContact(String identifier) {
        Contact contact;
        Lock writeLock = contactLock.writeLock();
        writeLock.lock();
        try {
            contact = contacts.get(identifier);
            if (contact == null) {
                contact = createContact(identifier);
                contacts.put(identifier, contact);
            }
        } finally {
            writeLock.unlock();
        }
        return contact;
    }

    private Contact getContact(StringValue identifier) {
        if (identifier == null) {
            return null;
        }
        return getContact(identifier.string);
    }

    //
    //  LocationDelegate
    //

    @Override
    public boolean storeLocation(LocationValue location) {
        StringValue identifier = location.getIdentifier();
        if (identifier == null) {
            // location ID not found
            return false;
        }
        // store by contact
        Contact contact = getContact(identifier.string);
        if (!contact.storeLocation(location)) {
            // location error
            return false;
        }
        // update the map
        SocketAddress address;
        SourceAddressValue sourceAddress = location.getSourceAddress();
        if (sourceAddress != null) {
            address = new InetSocketAddress(sourceAddress.ip, sourceAddress.port);
            locations.put(address, new WeakReference<>(location));
        }
        MappedAddressValue mappedAddress = location.getMappedAddress();
        if (mappedAddress != null) {
            address = new InetSocketAddress(mappedAddress.ip, mappedAddress.port);
            locations.put(address, new WeakReference<>(location));
        }
        return true;
    }

    @Override
    public boolean clearLocation(LocationValue location) {
        StringValue identifier = location.getIdentifier();
        if (identifier == null) {
            // location ID not found
            return false;
        }
        Contact contact = getContact(identifier.string);
        if (!contact.clearLocation(location)) {
            // location error
            return false;
        }
        // update the map
        SocketAddress address;
        SourceAddressValue sourceAddress = location.getSourceAddress();
        if (sourceAddress != null) {
            address = new InetSocketAddress(sourceAddress.ip, sourceAddress.port);
            locations.remove(address);
        }
        MappedAddressValue mappedAddress = location.getMappedAddress();
        if (mappedAddress != null) {
            address = new InetSocketAddress(mappedAddress.ip, mappedAddress.port);
            locations.remove(address);
        }
        return true;
    }

    @Override
    public LocationValue currentLocation() {
        if (identifier == null) {
            return null;
        }
        Contact contact = getContact(identifier);
        //contact.purge(peer);
        return contact.anyLocation();
    }

    @Override
    public LocationValue getLocation(SocketAddress address) {
        WeakReference<LocationValue> ref = locations.get(address);
        if (ref == null) {
            return null;
        }
        LocationValue location = ref.get();
        if (location == null) {
            return null;
        }
        Contact contact = getContact(location.getIdentifier());
        if (contact.isExpired(location, peer)) {
            return null;
        }
        return location;
    }

    @Override
    public List<LocationValue> getLocations(String identifier) {
        Contact contact = getContact(identifier);
        contact.purge(peer);
        return contact.allLocations();
    }

    @Override
    public LocationValue signLocation(LocationValue location) {
        StringValue idValue = location.getIdentifier();
        if (idValue == null || !identifier.equals(idValue.string)) {
            // ID not match
            return null;
        }
        // source address
        InetSocketAddress address = (InetSocketAddress) sourceAddress;
        SourceAddressValue addressValue = new SourceAddressValue(address.getHostString(), address.getPort());
        // timestamp
        long now = (new Date()).getTime() / 1000;
        TimestampValue timestampValue = new TimestampValue(now);
        // NAT type
        StringValue natValue = new StringValue(nat);
        // location value to be signed
        LocationValue value = LocationValue.create(location.getIdentifier(),
                addressValue, location.getMappedAddress(), location.getRelayedAddress(),
                timestampValue, null, natValue);
        Contact contact = getContact(identifier);
        return contact.signLocation(value);
    }
}
