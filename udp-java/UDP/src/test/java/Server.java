
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.UnknownHostException;
import java.nio.channels.DatagramChannel;
import java.nio.charset.StandardCharsets;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.udp.DiscreteChannel;
import chat.dim.udp.PackageHub;

class ServerHub extends PackageHub {

    private Connection connection = null;

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) throws IOException {
        if (connection == null) {
            connection = super.createConnection(remote, local);
        }
        return connection;
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        DatagramChannel sock = Server.master;
        if (sock == null) {
            return null;
        } else {
            return new DiscreteChannel(sock);
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
            hub.sendMessage(data, source, destination);
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
        try {
            hub.connect(null, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
        while (running) {
            hub.tick();
            clean();
            Client.idle(128);
        }
    }

    private void clean() {

    }

    static SocketAddress localAddress;
    static DatagramChannel master;

    private static ServerHub hub;

    public static void main(String[] args) throws IOException {

        Client.info("Starting server (" + HOST + ":" + PORT + ") ...");

        localAddress = new InetSocketAddress(HOST, PORT);
        master = DatagramChannel.open();
        master.socket().bind(localAddress);
        master.configureBlocking(false);

        Server server = new Server();

        hub = new ServerHub(server);

        server.start();
    }
}
