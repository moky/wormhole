
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

import chat.dim.net.BaseConnection;
import chat.dim.net.BaseHub;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.tcp.StreamChannel;

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

    public void onDataReceived(byte[] data, SocketAddress source, SocketAddress destination) {
        String text = new String(data, StandardCharsets.UTF_8);
        Client.info("<<< received (" + data.length + " bytes) from " + source + " to " + destination + ": " + text);
        text = (counter++) + "# " + data.length + " byte(s) received";
        data = text.getBytes(StandardCharsets.UTF_8);
        Client.info(">>> responding: " + text);
        send(data, destination, source);
    }
    static int counter = 0;

    private byte[] receive(SocketAddress source, SocketAddress destination) {
        return hub.receive(source, destination);
    }

    private boolean send(byte[] data, SocketAddress source, SocketAddress destination) {
        return hub.send(data, source, destination);
    }

    @Override
    public synchronized void start() {
        running = true;
        super.start();
    }

    @Override
    public void run() {
        SocketChannel channel;
        while (running) {
            try {
                channel = master.accept();
                if (channel != null) {
                    slaves.add(channel);
                } else if (!process()) {
                    Client.idle(128);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    private boolean process() throws IOException {
        int count = 0;
        byte[] data;
        SocketAddress remote;
        Set<SocketChannel> channels = new HashSet<>(slaves);
        // receive data
        for (SocketChannel item : channels) {
            remote = item.getRemoteAddress();
            data = receive(remote, localAddress);
            if (data != null && data.length > 0) {
                onDataReceived(data, remote, localAddress);
                ++count;
            }
        }
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
        return count > 0;
    }

    private static SocketAddress localAddress;
    private static ServerSocketChannel master;
    private static final Set<SocketChannel> slaves = new HashSet<>();

    private static Hub hub;
    private static Server server;

    public static void main(String[] args) throws IOException {

        Client.info("Starting server (" + HOST + ":" + PORT + ") ...");

        localAddress = new InetSocketAddress(HOST, PORT);
        master = ServerSocketChannel.open();
        master.socket().bind(localAddress);
        master.configureBlocking(false);

        hub = new BaseHub() {
            @Override
            protected Connection createConnection(SocketAddress remote, SocketAddress local) {
                SocketChannel sock = null;
                for (SocketChannel item : slaves) {
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
                }
                try {
                    BaseConnection conn = new BaseConnection(new StreamChannel(sock));
                    conn.setDelegate(server);
                    conn.start();
                    return conn;
                } catch (IOException e) {
                    e.printStackTrace();
                    return null;
                }
            }
        };

        server = new Server();
        server.start();
    }
}