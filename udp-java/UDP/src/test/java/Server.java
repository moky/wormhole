
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.channels.DatagramChannel;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.WeakHashMap;

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

public class Server implements Runnable, Connection.Delegate<Package> {

    private final SocketAddress localAddress;

    private final ServerHub hub;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        hub = new ServerHub(this);
    }

    @Override
    public void onConnectionStateChanged(Connection<Package> connection, ConnectionState previous, ConnectionState current) {
        Client.info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + previous + " -> " + current);
    }

    @Override
    public void onConnectionDataReceived(Connection<Package> connection, SocketAddress remote, Package pack) {
        byte[] payload = pack.body.getBytes();
        String text = new String(payload, StandardCharsets.UTF_8);
        Client.info("<<< received (" + payload.length + " bytes) from " + remote + ": " + text);
        text = (counter++) + "# " + payload.length + " byte(s) received";
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
        Client.info(">>> responding: " + text);
        send(data, localAddress, remote);
    }
    static int counter = 0;

    private void send(byte[] data, SocketAddress source, SocketAddress destination) {
        try {
            hub.sendMessage(data, source, destination);
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
                Client.idle(8);
            }
        }
    }

    static String HOST;
    static int PORT = 9394;

    static {
        try {
            HOST = Hub.getLocalAddressString();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {

        Client.info("Starting server (" + HOST + ":" + PORT + ") ...");

        Server server = new Server(new InetSocketAddress(HOST, PORT));

        server.start();
    }
}
