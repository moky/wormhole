
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

    public ServerConnection(Channel byteChannel) {
        super(byteChannel);
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
        Channel sock = createChannel(remote, local);
        ServerConnection connection = new ServerConnection(sock);
        // set delegate
        if (connection.getDelegate() == null) {
            connection.setDelegate(getDelegate());
        }
        // start FSM
        connection.start();
        return connection;
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) {
        if (remote != null) {
            Server.remoteAddress = remote;
        }
        return Server.masterChannel;
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
        try {
            hub.connect(remote, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void disconnect(SocketAddress remote) {
        try {
            hub.disconnect(remote, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected boolean sendPackage(Package pack, SocketAddress destination) {
        try {
            return hub.sendPackage(pack, localAddress, destination);
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
    }

    @Override
    protected Cargo receivePackage() {
        try {
            Package pack = hub.receivePackage(remoteAddress, localAddress);
            if (pack != null) {
                return new Cargo(remoteAddress, pack);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
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

    static final String SERVER_Test = "127.0.0.1"; // Test
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
