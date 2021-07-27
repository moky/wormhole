
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import chat.dim.dmtp.ContactManager;
import chat.dim.dmtp.LocationDelegate;
import chat.dim.dmtp.Session;
import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.LocationValue;
import chat.dim.dmtp.protocol.Message;
import chat.dim.mtp.Package;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.PackageConnection;
import chat.dim.type.Data;
import chat.dim.udp.ActivePackageHub;
import chat.dim.udp.DiscreteChannel;

class ClientHub extends ActivePackageHub {

    public ClientHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        Channel channel = new DiscreteChannel(remote, local);
        channel.configureBlocking(false);
        return channel;
    }
}

public class Client extends chat.dim.dmtp.Client {

    private SocketAddress serverAddress = null;

    private final ContactManager database;
    private final ActivePackageHub hub;

    public Client(String host, int port) {
        super(new InetSocketAddress(host, port));
        // database for location of contacts
        database = createContactManager();
        database.identifier = "moky-" + port;
        setDelegate(database);
        hub = new ClientHub(this);
    }

    @Override
    public void onConnectionStateChanging(Connection connection, ConnectionState current, ConnectionState next) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + current + " -> " + next);
        if (next.equals(ConnectionState.EXPIRED)) {
            assert connection instanceof PackageConnection : "connection error: " + connection;
            ((PackageConnection) connection).heartbeat(connection.getRemoteAddress());
        }
    }
    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }

    static void idle(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    protected ContactManager createContactManager() {
        ContactManager db = new ContactManager(this);
        db.identifier = "anyone@anywhere";
        return db;
    }

    public String getIdentifier() {
        return database.identifier;
    }

    @Override
    public Connection getConnection(SocketAddress remote) {
        return hub.getConnection(remote, localAddress);
    }

    @Override
    public void connect(SocketAddress remote) {
        try {
            hub.connect(remote, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void disconnect(SocketAddress remote) {
        try {
            hub.disconnect(remote, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
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

    @Override
    public boolean sendCommand(Command cmd, SocketAddress destination) {
        System.out.printf("sending cmd to %s: %s\n", destination, cmd);
        return super.sendCommand(cmd, destination);
    }

    @Override
    protected boolean sendPackage(Package pack, SocketAddress destination) {
        try {
            return hub.sendPackage(pack, localAddress, destination);
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
    }

    @Override
    protected Cargo receivePackage() {
        try {
            Package pack = hub.receivePackage(serverAddress, localAddress);
            if (pack != null) {
                return new Cargo(serverAddress, pack);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }

    @Override
    public boolean sendMessage(Message msg, SocketAddress destination) {
        System.out.printf("sending msg to %s: %s\n", destination, msg);
        return super.sendMessage(msg, destination);
    }

    @Override
    public boolean sayHello(SocketAddress destination) {
        if (super.sayHello(destination)) {
            return true;
        }
        Command cmd = Command.createHelloCommand(getIdentifier());
        sendCommand(cmd, destination);
        return true;
    }

    public boolean call(String identifier) {
        Command cmd = Command.createCallCommand(identifier);
        sendCommand(cmd, serverAddress);
        return true;
    }

    public void login(String identifier, SocketAddress remoteAddress) throws IOException {
        database.identifier = identifier;
        serverAddress = remoteAddress;
        hub.connect(remoteAddress, null);
        sayHello(remoteAddress);
    }

    public List<Session> getSessions(String receiver) {
        List<Session> sessions = new ArrayList<>();
        LocationDelegate delegate = getDelegate();
        assert delegate != null : "location delegate not set";
        List<LocationValue> locations = delegate.getLocations(receiver);
        SocketAddress sourceAddress;
        SocketAddress mappedAddress;
        Connection conn;
        ConnectionState state;
        for (LocationValue item : locations) {
            // source address
            sourceAddress = item.getSourceAddress();
            if (sourceAddress != null) {
                conn = getConnection(sourceAddress);
                if (conn != null) {
                    state = conn.getState();
                    if (state != null && (state.equals(ConnectionState.CONNECTED) ||
                            state.equals(ConnectionState.MAINTAINING) ||
                            state.equals(ConnectionState.EXPIRED))) {
                        sessions.add(new Session(item, sourceAddress));
                        continue;
                    }
                }
            }
            // mapped address
            mappedAddress = item.getMappedAddress();
            if (mappedAddress != null) {
                conn = getConnection(mappedAddress);
                if (conn != null) {
                    state = conn.getState();
                    if (state != null && (state.equals(ConnectionState.CONNECTED) ||
                            state.equals(ConnectionState.MAINTAINING) ||
                            state.equals(ConnectionState.EXPIRED))) {
                        sessions.add(new Session(item, mappedAddress));
                        //continue;
                    }
                }
            }
        }
        return sessions;
    }

    //
    //  test
    //

    void sendText(String receiver, String text) {
        List<Session> sessions = getSessions(receiver);
        if (sessions.size() == 0) {
            System.out.printf("user (%s) not login ...\n", receiver);
            // ask the server to help building a connection
            call(receiver);
            return;
        }
        long timestamp = (new Date()).getTime() / 1000;
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        Data content = new Data(bytes);
        Message msg = Message.create(getIdentifier(), receiver, timestamp, content, null, null);
        for (Session item : sessions) {
            System.out.printf("sending msg to %s:\n\t%s\n", item, msg);
            sendMessage(msg, item.address);
        }
    }

    static final String CLIENT_IP = "127.0.0.1";
    static final int CLIENT_PORT = Data.random(1).getByte(0) + 9900;

    public static void main(String[] args) throws IOException {

        SocketAddress serverAddress = new InetSocketAddress(Server.SERVER_IP, Server.SERVER_PORT);
        System.out.printf("connecting to UDP server: %s ...\n", serverAddress);

        String user = "moky-" + CLIENT_PORT;
        String friend = "moky";

        Client client = new Client(CLIENT_IP, CLIENT_PORT);
        client.start();

        client.login(user, serverAddress);

        // test send
        String text = "你好 " + friend + "!";
        int index = 0;
        while (index < 16777216) {
            idle(5000);
            System.out.printf("---- [%d]\n", index);
            client.sendText(friend, text + " (" + index + ")");
            ++index;
        }
    }
}
