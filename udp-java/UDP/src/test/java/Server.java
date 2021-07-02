
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.nio.charset.StandardCharsets;

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
            if (!process()) {
                Client.idle(128);
            }
        }
    }

    private boolean process() {
        byte[] data = hub.receive(remoteAddress, localAddress);
        if (data == null || data.length == 0) {
            return false;
        }
        onDataReceived(data, remoteAddress, localAddress);
        return true;
    }

    static SocketAddress localAddress;
    static SocketAddress remoteAddress;
    static DiscreteChannel masterChannel;

    private static ServerHub hub;

    public static void main(String[] args) throws IOException {

        Client.info("Starting server (" + HOST + ":" + PORT + ") ...");

        localAddress = new InetSocketAddress(HOST, PORT);
        remoteAddress = null;
        masterChannel = new DiscreteChannel(DatagramChannel.open());
        masterChannel.bind(localAddress);
        masterChannel.configureBlocking(false);

        Server server = new Server();

        hub = new ServerHub(server);

        server.start();
    }
}
