
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.WeakHashMap;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.net.RawDataHub;
import chat.dim.tcp.StreamChannel;

class ServerHub extends RawDataHub implements Runnable {

    private final Map<SocketAddress, SocketChannel> slaves = new WeakHashMap<>();
    private SocketAddress localAddress = null;
    private ServerSocketChannel master = null;
    private boolean running = false;

    public ServerHub(Connection.Delegate<byte[]> delegate) {
        super(delegate);
    }

    void bind(SocketAddress local) throws IOException {
        ServerSocketChannel sock = master;
        if (sock != null && sock.isOpen()) {
            sock.close();
        }
        sock = ServerSocketChannel.open();
        sock.socket().bind(local);
        sock.configureBlocking(false);
        master = sock;
        localAddress = local;
    }

    boolean isRunning() {
        return running;
    }

    void start() {
        running = true;
        new Thread(this).start();
    }

    void stop() {
        running = false;
    }

    @Override
    public void run() {
        SocketChannel channel;
        SocketAddress remote;
        while (running) {
            try {
                channel = master.accept();
                if (channel != null) {
                    remote = channel.getRemoteAddress();
                    slaves.put(remote, channel);
                    connect(remote, localAddress);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        SocketChannel sock = slaves.get(remote);
        if (sock == null) {
            throw new SocketException("failed to get channel: " + remote + " -> " + local);
        } else {
            return new StreamChannel(sock);
        }
    }
}

public class Server implements Runnable, Connection.Delegate<byte[]> {

    private final SocketAddress localAddress;

    private final ServerHub hub;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        hub = new ServerHub(this);
    }

    @Override
    public void onConnectionStateChanged(Connection<byte[]> connection, ConnectionState previous, ConnectionState current) {
        Client.info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + previous + " -> " + current);
    }

    @Override
    public void onConnectionDataReceived(Connection<byte[]> connection, SocketAddress remote, byte[] pack) {
        String text = new String(pack, StandardCharsets.UTF_8);
        Client.info("<<< received (" + pack.length + " bytes) from " + remote + ": " + text);
        text = (counter++) + "# " + pack.length + " byte(s) received";
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
        Client.info(">>> responding: " + text);
        send(data, localAddress, remote);
    }
    static int counter = 0;

    private void send(byte[] data, SocketAddress source, SocketAddress destination) {
        try {
            boolean ok = hub.send(data, source, destination);
            assert ok;
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
    static final int PORT = 9394;

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
