
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.udp.ActiveHub;
import chat.dim.udp.DiscreteChannel;
import chat.dim.udp.PackageConnection;

class ServerHub extends ActiveHub {

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    public void bind(SocketAddress local) throws IOException {
        getConnection(null, local);
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) throws IOException {
        DiscreteChannel channel = new DiscreteChannel();
        channel.bind(Server.localAddress);
        PackageConnection connection = new PackageConnection(channel);
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
        while (true) {
            try {
                if (!process()) {
                    idle();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    private boolean process() throws IOException {
        int count = 0;
        byte[] data = hub.receive(null, localAddress);
        if (data != null && data.length > 0) {
            onDataReceived(data, null, localAddress);
            ++count;
        }
        return count > 0;
    }

    static SocketAddress localAddress;

    private static final Set<SocketAddress> remoteAddresses = new HashSet<>();

    private static ServerHub hub;
    private static Server server;

    public static void main(String[] args) throws IOException {

        info("Starting server (" + HOST + ":" + PORT + ") ...");

        localAddress = new InetSocketAddress(HOST, PORT);

        server = new Server();

        hub = new ServerHub(server);
        hub.bind(localAddress);

        server.start();
    }
}
