
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.UnknownHostException;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.tcp.StreamChannel;
import chat.dim.tcp.StreamHub;

class ServerHub extends StreamHub {

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        SocketChannel sock = null;
        for (SocketChannel item : Server.slaves) {
            try {
                if (item.getRemoteAddress().equals(remote)) {
                    sock = item;
                    break;
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        if (sock == null) {
            return null;
        } else {
            return new StreamChannel(sock);
        }
    }
}

public class Server extends Thread implements Connection.Delegate {

    static InetAddress HOST;
    static int PORT = 9394;

    static {
        try {
            HOST = InetAddress.getLocalHost();
        } catch (UnknownHostException e) {
            e.printStackTrace();
        }
    }

    private boolean running = false;

    @Override
    public void onConnectionStateChanging(Connection connection, ConnectionState current, ConnectionState next) {
        Client.info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + current + " -> " + next);
    }

    @Override
    public void onConnectionReceivedData(Connection connection, SocketAddress remote, byte[] data) {
        String text = new String(data, StandardCharsets.UTF_8);
        Client.info("<<< received (" + data.length + " bytes) from " + remote + ": " + text);
        text = (counter++) + "# " + data.length + " byte(s) received";
        data = text.getBytes(StandardCharsets.UTF_8);
        Client.info(">>> responding: " + text);
        send(data, localAddress, remote);
    }
    static int counter = 0;

    private void send(byte[] data, SocketAddress source, SocketAddress destination) {
        try {
            hub.send(data, source, destination);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public synchronized void start() {
        running = true;
        super.start();
    }

    @Override
    public void run() {
        SocketChannel channel;
        SocketAddress remote, local;
        Connection conn;
        while (running) {
            try {
                channel = master.accept();
                if (channel != null) {
                    slaves.add(channel);
                    remote = channel.getRemoteAddress();
                    local = channel.getLocalAddress();
                    conn = hub.connect(remote, local);
                    assert conn != null : "connection error: " + remote + ", " + local;
                } else {
                    hub.tick();
                    clean();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
            Client.idle(128);
        }
    }

    private void clean() {
        Set<SocketChannel> channels = new HashSet<>(slaves);
        // check closed channels
        Set<SocketChannel> dying = new HashSet<>();
        for (SocketChannel item : channels) {
            if (!item.isOpen()) {
                dying.add(item);
            }
        }
        if (dying.size() > 0) {
            Client.info(dying.size() + " channel(s) dying");
            for (SocketChannel item : dying) {
                slaves.remove(item);
            }
        }
        if (slaves.size() > 0) {
            Client.info(slaves.size() + " channel(s) alive");
        }
    }

    static SocketAddress localAddress;
    static ServerSocketChannel master;
    static final Set<SocketChannel> slaves = new HashSet<>();

    private static ServerHub hub;

    public static void main(String[] args) throws IOException {

        Client.info("Starting server (" + HOST + ":" + PORT + ") ...");

        localAddress = new InetSocketAddress(HOST, PORT);
        master = ServerSocketChannel.open();
        master.socket().bind(localAddress);
        master.configureBlocking(false);

        Server server = new Server();

        hub = new ServerHub(server);

        server.start();
    }
}
