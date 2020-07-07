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

    public String nat = "Unknown";
    private final SocketAddress sourceAddress;

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
        String identifier = location.getIdentifier();
        if (identifier == null) {
            // location ID not found
            return false;
        }
        // store by contact
        Contact contact = getContact(identifier);
        if (!contact.storeLocation(location)) {
            // location error
            return false;
        }
        // update the map
        SocketAddress sourceAddress = location.getSourceAddress();
        if (sourceAddress != null) {
            locations.put(sourceAddress, new WeakReference<>(location));
        }
        SocketAddress mappedAddress = location.getMappedAddress();
        if (mappedAddress != null) {
            locations.put(mappedAddress, new WeakReference<>(location));
        }
        return true;
    }

    @Override
    public boolean clearLocation(LocationValue location) {
        String identifier = location.getIdentifier();
        if (identifier == null) {
            // location ID not found
            return false;
        }
        Contact contact = getContact(identifier);
        if (!contact.clearLocation(location)) {
            // location error
            return false;
        }
        // update the map
        SocketAddress sourceAddress = location.getSourceAddress();
        if (sourceAddress != null) {
            locations.remove(sourceAddress);
        }
        SocketAddress mappedAddress = location.getMappedAddress();
        if (mappedAddress != null) {
            locations.remove(mappedAddress);
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
        return contact.getLocation(sourceAddress);
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
        if (Contact.isExpired(location, peer)) {
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
        if (!identifier.equals(location.getIdentifier())) {
            // ID not match
            return null;
        }
        // timestamp
        long now = (new Date()).getTime() / 1000;
        // location value to be signed
        LocationValue value = LocationValue.create(location.getIdentifier(),
                sourceAddress, location.getMappedAddress(), location.getRelayedAddress(),
                now, null, nat);
        Contact contact = getContact(identifier);
        return contact.signLocation(value);
    }
}
