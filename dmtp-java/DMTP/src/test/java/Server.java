
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.channels.DatagramChannel;
import java.util.Map;
import java.util.WeakHashMap;

import chat.dim.dmtp.ContactManager;
import chat.dim.dmtp.Server;
import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.Message;
import chat.dim.mtp.Package;
import chat.dim.mtp.PackageHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.udp.PackageChannel;

class ServerHub extends PackageHub {

    private final Map<SocketAddress, Connection<Package>> connections = new WeakHashMap<>();
    private final Map<SocketAddress, DatagramChannel> channels = new WeakHashMap<>();
    private boolean running = false;

    public ServerHub(Connection.Delegate<Package> delegate) {
        super(delegate);
    }

    void bind(SocketAddress local) throws IOException {
        DatagramChannel sock = channels.get(local);
        if (sock == null) {
            sock = DatagramChannel.open();
            sock.socket().bind(local);
            sock.configureBlocking(false);
            channels.put(local, sock);
        }
        connect(null, local);
    }

    boolean isRunning() {
        return running;
    }

    void start() {
        running = true;
    }

    void stop() {
        running = false;
    }

    @Override
    protected Connection<Package> createConnection(SocketAddress remote, SocketAddress local) throws IOException {
        Connection<Package> conn = connections.get(local);
        if (conn == null) {
            conn = super.createConnection(remote, local);
            connections.put(local, conn);
        }
        return conn;
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        DatagramChannel sock = channels.get(local);
        if (sock == null) {
            throw new SocketException("failed to get channel: " + remote + " -> " + local);
        } else {
            return new PackageChannel(sock);
        }
    }
}

class DmtpServer extends Server implements Runnable, Connection.Delegate<Package> {

    private final SocketAddress localAddress;

    private final ServerHub hub;

    public DmtpServer(SocketAddress local) {
        super();
        localAddress = local;
        hub = new ServerHub(this);
    }

    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }

    static void idle(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void connect(SocketAddress remote) {
        try {
            hub.connect(remote, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void start() {
        try {
            hub.bind(localAddress);
            hub.start();
        } catch (IOException e) {
            e.printStackTrace();
        }
        new Thread(this).start();
    }

    void stop() {
        hub.stop();
    }

    @Override
    public void run() {
        while (hub.isRunning()) {
            hub.tick();
            if (hub.getActivatedCount() == 0) {
                idle(8);
            }
        }
    }

    @Override
    public void onConnectionStateChanged(Connection connection, ConnectionState previous, ConnectionState current) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + previous + " -> " + current);
    }

    @Override
    public void onConnectionDataReceived(Connection<Package> connection, SocketAddress remote, Package pack) {
        onReceivedPackage(remote, pack);
    }

    @Override
    public boolean sendMessage(Message msg, SocketAddress destination) {
        try {
            hub.sendMessage(msg.getBytes(), localAddress, destination);
            return true;
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
    }

    @Override
    public boolean sendCommand(Command cmd, SocketAddress destination) {
        try {
            hub.sendCommand(cmd.getBytes(), localAddress, destination);
            return true;
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
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

    static String HOST;
    static int PORT = 9395;

    static {
        try {
            HOST = Hub.getLocalAddressString();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    static ContactManager database;

    public static void main(String[] args) {

        System.out.printf("UDP server (%s:%d) starting ...\n", HOST, PORT);

        DmtpServer server = new DmtpServer(new InetSocketAddress(HOST, PORT));

        // database for location of contacts
        database = new ContactManager(server.hub, server.localAddress);
        database.identifier = "station@anywhere";
        server.setDelegate(database);

        server.start();
    }
}
