
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import chat.dim.dmtp.Client;
import chat.dim.dmtp.ContactManager;
import chat.dim.dmtp.LocationDelegate;
import chat.dim.dmtp.Session;
import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.LocationValue;
import chat.dim.dmtp.protocol.Message;
import chat.dim.mtp.ActivePackageHub;
import chat.dim.mtp.Package;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.type.Data;
import chat.dim.udp.PackageChannel;

class ClientHub extends ActivePackageHub {

    private boolean running = false;

    public ClientHub(Connection.Delegate<Package> delegate) {
        super(delegate);
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
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        Channel channel = new PackageChannel(remote, local);
        channel.configureBlocking(false);
        return channel;
    }
}

class DmtpClient extends Client implements Runnable, Connection.Delegate<Package> {

    private final SocketAddress localAddress;
    private final SocketAddress remoteAddress;
    private final ClientHub hub;

    DmtpClient(SocketAddress local, SocketAddress remote) {
        super();
        localAddress = local;
        remoteAddress = remote;
        hub = new ClientHub(this);
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

    private String getIdentifier() {
        return database.identifier;
    }

    @Override
    public void connect(SocketAddress remote) {
        try {
            hub.connect(remote, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    private void disconnect() {
        try {
            hub.disconnect(remoteAddress, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void start() {
        try {
            hub.connect(remoteAddress, localAddress);
            hub.start();
        } catch (IOException e) {
            e.printStackTrace();
        }
        new Thread(this).start();
    }

    void stop() {
        disconnect();
        hub.stop();
    }

    @Override
    public void run() {
        while (hub.isRunning()) {
            hub.tick();
            if (hub.getActivatedCount() == 0) {
                idle(8);
            }
        }
    }

    @Override
    public void onConnectionStateChanged(Connection connection, ConnectionState previous, ConnectionState current) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + previous + " -> " + current);
    }

    @Override
    public void onConnectionDataReceived(Connection<Package> connection, SocketAddress remote, Package pack) {
        onReceivedPackage(remote, pack);
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
        sendCommand(cmd, remoteAddress);
        return true;
    }

    public void login(String identifier) throws IOException {
        database.identifier = identifier;
        hub.connect(remoteAddress, null);
        sayHello(remoteAddress);
    }

    public List<Session> getSessions(String receiver) throws IOException {
        List<Session> sessions = new ArrayList<>();
        LocationDelegate delegate = getDelegate();
        assert delegate != null : "location delegate not set";
        List<LocationValue> locations = delegate.getLocations(receiver);
        SocketAddress sourceAddress;
        SocketAddress mappedAddress;
        Connection<Package> conn;
        ConnectionState state;
        for (LocationValue item : locations) {
            // source address
            sourceAddress = item.getSourceAddress();
            if (sourceAddress != null) {
                conn = hub.connect(sourceAddress, localAddress);
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
                conn = hub.connect(mappedAddress, localAddress);
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

    void sendText(String receiver, String text) throws IOException {
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

    void test(String friend) throws IOException {

        // test send
        String text = "你好 " + friend + "!";
        int index = 0;
        while (index < 16777216) {
            idle(5000);
            System.out.printf("---- [%d]\n", index);
            sendText(friend, text + " (" + index + ")");
            ++index;
        }
    }

    static String HOST;
    static final int PORT = Data.random(1).getByte(0) + 9900;

    static {
        try {
            HOST = Hub.getLocalAddressString();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    static ContactManager database;

    public static void main(String[] args) throws IOException {

        SocketAddress local = new InetSocketAddress(HOST, PORT);
        SocketAddress remote = new InetSocketAddress(DmtpServer.HOST, DmtpServer.PORT);
        System.out.printf("connecting to UDP server: %s ...\n", remote);

        String user = "moky-" + PORT;
        String friend = "moky";

        DmtpClient client = new DmtpClient(local, remote);

        // database for location of contacts
        database = new ContactManager(client.hub, client.localAddress);
        database.identifier = "moky-" + PORT;
        client.setDelegate(database);

        client.start();
        client.login(user);
        client.test(friend);
        client.stop();
    }
}
