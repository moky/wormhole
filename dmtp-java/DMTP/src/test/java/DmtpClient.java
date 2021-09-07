
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
import chat.dim.mtp.Package;
import chat.dim.mtp.PackageArrival;
import chat.dim.mtp.PackageDeparture;
import chat.dim.mtp.TransactionID;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.port.Gate;
import chat.dim.type.Data;
import chat.dim.udp.ClientHub;

public class DmtpClient extends Client implements Gate.Delegate<PackageDeparture, PackageArrival, TransactionID> {

    private final SocketAddress localAddress;
    private final SocketAddress remoteAddress;

    private final UDPGate<ClientHub> gate;

    DmtpClient(SocketAddress local, SocketAddress remote) {
        super();
        localAddress = local;
        remoteAddress = remote;
        gate = new UDPGate<>(this);
        gate.hub = new ClientHub(gate);
    }

    private String getIdentifier() {
        return database.identifier;
    }

    @Override
    public void connect(SocketAddress remote) {
        try {
            gate.connect(remote, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void start() throws IOException {
        gate.hub.bind(localAddress);
        gate.connect(remoteAddress, localAddress);
        gate.start();
    }

    void stop() {
        gate.stop();
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        UDPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(PackageArrival ship, SocketAddress source, SocketAddress destination, Gate gate) {
        Package pack = ship.getPackage();
        onReceivedPackage(source, pack);
    }

    @Override
    public void onSent(PackageDeparture ship, SocketAddress source, SocketAddress destination, Gate gate) {
        Package pack = ship.getPackage();
        int bodyLen = pack.head.bodyLength;
        if (bodyLen == -1) {
            bodyLen = pack.body.getSize();
        }
        UDPGate.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onError(Error error, PackageDeparture ship, SocketAddress source, SocketAddress destination, Gate gate) {
        UDPGate.error(error.getMessage());
    }

    //
    //  Client Interfaces
    //

    @Override
    public boolean sendMessage(Message msg, SocketAddress destination) {
        gate.sendMessage(msg.getBytes(), localAddress, destination);
        return true;
    }

    @Override
    public boolean sendCommand(Command cmd, SocketAddress destination) {
        gate.sendCommand(cmd.getBytes(), localAddress, destination);
        return true;
    }

    @Override
    public boolean processCommand(Command cmd, SocketAddress source) {
        UDPGate.info("received cmd from " + source + ": " + cmd);
        return super.processCommand(cmd, source);
    }

    @Override
    public boolean processMessage(Message msg, SocketAddress source) {
        UDPGate.info("received msg from " + source + ": " + msg);
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
        gate.connect(remoteAddress, localAddress);
        sayHello(remoteAddress);
    }

    public List<Session> getSessions(String receiver) throws IOException {
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
                conn = gate.connect(sourceAddress, localAddress);
                if (conn != null) {
                    state = conn.getState();
                    if (state != null && (state.equals(ConnectionState.READY) ||
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
                conn = gate.connect(mappedAddress, localAddress);
                if (conn != null) {
                    state = conn.getState();
                    if (state != null && (state.equals(ConnectionState.READY) ||
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
            UDPGate.error("user (" + receiver + ") not login ...");
            // ask the server to help building a connection
            call(receiver);
            return;
        }
        long timestamp = (new Date()).getTime() / 1000;
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        Data content = new Data(bytes);
        Message msg = Message.create(getIdentifier(), receiver, timestamp, content, null, null);
        for (Session item : sessions) {
            UDPGate.info("sending msg to " + item + ":\n\t" + msg);
            sendMessage(msg, item.address);
        }
    }

    void test(String friend) throws IOException {

        // test send
        String text = "你好 " + friend + "!";
        int index = 0;
        while (index < 16777216) {
            UDPGate.idle(5000);
            UDPGate.info("---- [" + index + "]");
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
        UDPGate.info("Connecting to DMTP server: " + remote + " ...");

        String user = "moky-" + PORT;
        String friend = "moky";

        DmtpClient client = new DmtpClient(local, remote);

        // database for location of contacts
        database = new ContactManager(client.gate.hub, client.localAddress);
        database.identifier = "moky-" + PORT;
        client.setDelegate(database);

        client.start();
        client.login(user);
        client.test(friend);
        client.stop();
    }
}
