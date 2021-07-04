
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;

import chat.dim.dmtp.ContactManager;
import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.Message;
import chat.dim.mtp.Package;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.PackageConnection;
import chat.dim.udp.ActivePackageHub;
import chat.dim.udp.DiscreteChannel;

class ServerConnection extends PackageConnection {

    public ServerConnection(Channel byteChannel, SocketAddress remote, SocketAddress local) {
        super(byteChannel, remote, local);
    }

    @Override
    protected Channel connect(SocketAddress remote, SocketAddress local) {
        return Server.masterChannel;
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        SocketAddress remote = super.receive(dst);
        if (remote != null) {
            Server.remoteAddress = remote;
        }
        return remote;
    }
}

class ServerHub extends ActivePackageHub {

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) {
        ServerConnection conn = new ServerConnection(Server.masterChannel, Server.remoteAddress, Server.localAddress);
        // set delegate
        Connection.Delegate delegate = getDelegate();
        if (delegate != null) {
            conn.setDelegate(delegate);
        }
        // start FSM
        conn.start();
        return conn;
    }
}

public class Server extends chat.dim.dmtp.Server implements Runnable {

    private final ServerHub hub;

    public Server(String host, int port) {
        super(new InetSocketAddress(host, port));
        // database for location of contacts
        database = createContactManager();
        setDelegate(database);
        hub = new ServerHub(this);
    }

    @Override
    public void onConnectionStateChanging(Connection connection, ConnectionState current, ConnectionState next) {
        Client.info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + current + " -> " + next);
        if (next.equals(ConnectionState.EXPIRED)) {
            assert connection instanceof PackageConnection : "connection error: " + connection;
            ((PackageConnection) connection).heartbeat(connection.getRemoteAddress());
        }
    }

    protected ContactManager createContactManager() {
        ContactManager db = new ContactManager(this);
        db.identifier = "station@anywhere";
        return db;
    }

    @Override
    public Connection getConnection(SocketAddress remote) {
        return hub.getConnection(remote, localAddress);
    }

    @Override
    public void connect(SocketAddress remote) {
        hub.connect(remote, localAddress);
    }

    @Override
    public void disconnect(SocketAddress remote) {
        hub.disconnect(remote, localAddress);
    }

    @Override
    protected boolean sendPackage(Package pack, SocketAddress destination) {
        return hub.sendPackage(pack, localAddress, destination);
    }

    @Override
    protected Cargo receivePackage() {
        Package pack = hub.receivePackage(remoteAddress, localAddress);
        return pack == null ? null : new Cargo(remoteAddress, pack);
    }

    @Override
    public boolean processCommand(Command cmd, SocketAddress source) {
        System.out.printf("received cmd from %s: %s\n", source, cmd);
        return super.processCommand(cmd, source);
    }

    @Override
    public boolean processMessage(Message msg, SocketAddress source) {
        System.out.printf("received msg from %s: %s\n", source, msg);
        return true;
    }

    static final String SERVER_Test = "192.168.31.91"; // Test
    static final String SERVER_GZ1 = "134.175.87.98"; // GZ-1
    static final String SERVER_HK2 = "129.226.128.17"; // HK-2

    static final String SERVER_IP = SERVER_Test;
    static final int SERVER_PORT = 9395;

    static Server server;
    static ContactManager database;

    static SocketAddress localAddress;
    static SocketAddress remoteAddress;
    static DiscreteChannel masterChannel;

    public static void main(String[] args) throws IOException {

        System.out.printf("UDP server (%s:%d) starting ...\n", SERVER_IP, SERVER_PORT);

        localAddress = new InetSocketAddress(SERVER_IP, SERVER_PORT);
        remoteAddress = null;
        masterChannel = new DiscreteChannel(DatagramChannel.open());
        masterChannel.bind(localAddress);
        masterChannel.configureBlocking(false);

        server = new Server(SERVER_IP, SERVER_PORT);

        database = new ContactManager(server);

        server.setDelegate(database);
        server.start();
    }
}
