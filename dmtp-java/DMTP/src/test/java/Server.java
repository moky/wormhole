
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.channels.DatagramChannel;

import chat.dim.dmtp.ContactManager;
import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.Message;
import chat.dim.mtp.Header;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.type.Data;
import chat.dim.udp.DiscreteChannel;
import chat.dim.udp.PackageHub;

class ServerHub extends PackageHub {

    private Connection connection = null;

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    public void bind(SocketAddress local) throws IOException {
        connect(null, local);
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

public class Server extends chat.dim.dmtp.Server implements Runnable, Connection.Delegate {

    private boolean running;

    public Server() {
        super();
        running = false;
    }

    @Override
    protected void connect(SocketAddress remote) {
        try {
            hub.connect(remote, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void run() {
        try {
            hub.bind(localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }

        running = true;
        while (running) {
            hub.tick();
            Client.idle(128);
        }
    }

    @Override
    public void onConnectionStateChanging(Connection connection, ConnectionState current, ConnectionState next) {
        Client.info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + current + " -> " + next);
    }

    @Override
    public void onConnectionDataReceived(Connection connection, SocketAddress remote, Object wrapper, byte[] payload) {
        if (wrapper instanceof Header && payload != null && payload.length > 0) {
            onReceivedPackage(remote, (Header) wrapper, new Data(payload));
        }
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

    static SocketAddress localAddress;
    static DatagramChannel master;

    static ServerHub hub;

    public static void main(String[] args) throws IOException {

        System.out.printf("UDP server (%s:%d) starting ...\n", HOST, PORT);

        localAddress = new InetSocketAddress(HOST, PORT);
        master = DatagramChannel.open();
        master.socket().bind(localAddress);
        master.configureBlocking(false);

        Server server = new Server();

        hub = new ServerHub(server);

        // database for location of contacts
        database = new ContactManager(hub, localAddress);
        database.identifier = "station@anywhere";
        server.setDelegate(database);

        new Thread(server).start();
    }
}
