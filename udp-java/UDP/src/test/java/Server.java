
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

import chat.dim.net.BaseConnection;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.udp.ActivePackageHub;
import chat.dim.udp.DiscreteChannel;

class ServerConnection extends BaseConnection {

    public ServerConnection(Channel byteChannel) {
        super(byteChannel);
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        SocketAddress remote = super.receive(dst);
        if (remote != null) {
            Server.remoteAddresses.add(remote);
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
        ServerConnection connection = new ServerConnection(Server.masterChannel);
        // set delegate
        Connection.Delegate delegate = getDelegate();
        if (delegate != null) {
            connection.setDelegate(delegate);
        }
        // start FSM
        connection.start();
        return connection;
    }
}

public class Server extends Thread implements Connection.Delegate {

    static String HOST = "192.168.31.91";
    static int PORT = 9394;

    private boolean running = false;

    @Override
    public void onConnectionStateChanged(Connection connection, ConnectionState oldStatus, ConnectionState newStatus) {
        Client.info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + oldStatus + " -> "
                + newStatus);
    }

    public void onDataReceived(byte[] data, SocketAddress source, SocketAddress destination) {
        String text = new String(data, StandardCharsets.UTF_8);
        Client.info("<<< received (" + data.length + " bytes) from " + source + " to " + destination + ": " + text);
        text = (++counter) + "# " + data.length + " byte(s) received";
        data = text.getBytes(StandardCharsets.UTF_8);
        Client.info(">>> responding: " + text);
        hub.send(data, destination, source);
    }
    static int counter = 0;

    @Override
    public synchronized void start() {
        running = true;
        super.start();
    }

    @Override
    public void run() {
        while (running) {
            try {
                if (!process()) {
                    Client.idle(128);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    private boolean process() throws IOException {
        if (remoteAddresses.size() == 0) {
            return process(null);
        }
        int count = 0;
        Set<SocketAddress> addresses = new HashSet<>(remoteAddresses);
        for (SocketAddress remote : addresses) {
            if (process(remote)) {
                ++count;
            }
        }
        return count > 0;
    }

    private boolean process(SocketAddress remote) {
        byte[] data = hub.receive(remote, localAddress);
        if (data == null || data.length == 0) {
            return false;
        }
        onDataReceived(data, remote, localAddress);
        return true;
    }

    static SocketAddress localAddress;
    static DiscreteChannel masterChannel;
    static final Set<SocketAddress> remoteAddresses = new HashSet<>();

    private static ServerHub hub;

    public static void main(String[] args) throws IOException {

        Client.info("Starting server (" + HOST + ":" + PORT + ") ...");

        localAddress = new InetSocketAddress(HOST, PORT);
        masterChannel = new DiscreteChannel(DatagramChannel.open());
        masterChannel.bind(localAddress);
        masterChannel.configureBlocking(false);

        Server server = new Server();

        hub = new ServerHub(server);

        server.start();
    }
}
