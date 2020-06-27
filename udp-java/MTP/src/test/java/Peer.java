
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;

import chat.dim.mtp.Pool;
import chat.dim.mtp.protocol.Package;
import chat.dim.mtp.task.Arrival;
import chat.dim.mtp.task.Departure;
import chat.dim.udp.Connection;
import chat.dim.udp.ConnectionStatus;
import chat.dim.udp.HubFilter;
import chat.dim.udp.HubListener;

public class Peer extends chat.dim.mtp.Peer implements HubListener {

    public final SocketAddress localAddress;
    public final Hub hub;

    public Peer(SocketAddress address, Hub hub, Pool pool) {
        super(pool);
        this.localAddress = address;
        this.hub = hub;
        hub.addListener(this);
        this.setDelegate(hub);
    }

    public Peer(SocketAddress address, Hub hub) {
        super();
        this.localAddress = address;
        this.hub = hub;
        hub.addListener(this);
        this.setDelegate(hub);
    }

    public Peer(SocketAddress address, Pool pool) throws SocketException {
        this(address, createHub(address), pool);
    }

    public Peer(SocketAddress address) throws SocketException {
        this(address, createHub(address));
    }

    public Peer(String host, int port, Pool pool) throws SocketException {
        this(new InetSocketAddress(host, port), pool);
    }

    public Peer(String host, int port) throws SocketException {
        this(new InetSocketAddress(host, port));
    }

    private static Hub createHub(SocketAddress localAddress) throws SocketException {
        InetSocketAddress address = (InetSocketAddress) localAddress;
        Hub hub = new Hub();
        hub.open(address.getHostString(), address.getPort());
        //hub.start();
        return hub;
    }

    @Override
    public void start() {
        // start peer
        super.start();
        // start hub
        hub.start();
    }

    @Override
    public void close() {
        // stop hub
        hub.close();
        // stop peer
        super.close();
    }

    public Departure sendCommand(Package pack, SocketAddress destination) {
        return sendCommand(pack, destination, localAddress);
    }

    public Departure sendMessage(Package pack, SocketAddress destination) {
        return sendMessage(pack, destination, localAddress);
    }

    //
    //  HubListener
    //

    @Override
    public HubFilter getFilter() {
        return null;
    }

    @Override
    public byte[] onDataReceived(byte[] data, SocketAddress source, SocketAddress destination) {
        Arrival task = new Arrival(data, source, destination);
        pool.appendArrival(task);
        return null;
    }

    @Override
    public void onStatusChanged(Connection connection, ConnectionStatus oldStatus, ConnectionStatus newStatus) {

    }
}
