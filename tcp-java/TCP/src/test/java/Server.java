
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
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

    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }
    static void info(byte[] data) {
        info(new String(data, StandardCharsets.UTF_8));
    }

    static void idle() {
        try {
            Thread.sleep(200);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    static String HOST = "192.168.31.91";
    static int PORT = 9394;

    @Override
    public void onConnectionStateChanged(Connection connection, ConnectionState oldStatus, ConnectionState newStatus) {
        info("!!! connection state changed: " + oldStatus + " -> " + newStatus);
    }

    public void onDataReceived(byte[] data, SocketAddress source, SocketAddress destination) {
        String text = new String(data, StandardCharsets.UTF_8);
        info("<<< received (" + data.length + " bytes) from " + source + " to " + destination + ": " + text);
        text = data.length + " byte(s) received";
        data = text.getBytes(StandardCharsets.UTF_8);
        info(">>> responding: " + text);
        hub.send(data, destination, source);
    }

    @Override
    public void run() {
        SocketChannel channel;
        while (true) {
            try {
                channel = master.accept();
                if (channel != null) {
                    slaves.add(channel);
                } else if (!process()) {
                    idle();
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
        Set<SocketChannel> dying = new HashSet<>();
        for (SocketChannel item : slaves) {
            if (!item.isOpen()) {
                dying.add(item);
                continue;
            }
            remote = item.getRemoteAddress();
            data = hub.receive(remote, localAddress);
            if (data != null && data.length > 0) {
                onDataReceived(data, remote, localAddress);
                ++count;
            }
        }
        if (dying.size() > 0) {
            info(dying.size() + " channel(s) dying");
            for (SocketChannel item : dying) {
                slaves.remove(item);
            }
        }
        if (slaves.size() > 0) {
            info(slaves.size() + " channel(s) alive");
        }
        return count > 0;
    }

    private static SocketAddress localAddress;
    private static ServerSocketChannel master;
    private static final Set<SocketChannel> slaves = new HashSet<>();

    private static Hub hub;
    private static Server server;

    public static void main(String[] args) throws IOException {

        info("Starting server (" + HOST + ":" + PORT + ") ...");

        localAddress = new InetSocketAddress(HOST, PORT);
        master = ServerSocketChannel.open();
        master.socket().bind(localAddress);
        master.configureBlocking(false);

        hub = new BaseHub() {
            @Override
            protected Connection createConnection(SocketAddress remote, SocketAddress local) throws IOException {
                SocketChannel sock = null;
                for (SocketChannel item : slaves) {
                    if (item.getRemoteAddress().equals(remote)) {
                        sock = item;
                        break;
                    }
                }
                if (sock == null) {
                    return null;
                }
                StreamChannel channel = new StreamChannel(sock);
                BaseConnection connection = new BaseConnection(channel);
                connection.setDelegate(server);
                connection.start();
                return connection;
            }
        };

        server = new Server();
        server.start();
    }
}
