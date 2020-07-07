
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import chat.dim.dmtp.ContactManager;
import chat.dim.dmtp.LocationDelegate;
import chat.dim.dmtp.Session;
import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.Message;
import chat.dim.dmtp.values.LocationValue;
import chat.dim.mtp.task.Departure;
import chat.dim.tlv.Data;
import chat.dim.udp.Connection;

public class Client extends chat.dim.dmtp.Client {

    private String identifier;
    private SocketAddress serverAddress = null;
    public String nat = "Unknown";

    private final ContactManager database;

    public Client(String host, int port) throws SocketException {
        super(new InetSocketAddress(host, port));
        database = new ContactManager(peer);
        setDelegate(database);
        identifier = "moky-" + port;
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
    public Departure sendCommand(Command cmd, SocketAddress destination) {
        System.out.printf("sending cmd to %s: %s\n", destination, cmd);
        return super.sendCommand(cmd, destination);
    }

    @Override
    public Departure sendMessage(Message msg, SocketAddress destination) {
        System.out.printf("sending msg to %s: %s\n", destination, msg);
        return super.sendMessage(msg, destination);
    }

    @Override
    public boolean sayHello(SocketAddress destination) {
        if (super.sayHello(destination)) {
            return true;
        }
        Command cmd = Command.Hello.create(identifier);
        sendCommand(cmd, destination);
        return true;
    }

    public boolean call(String identifier) {
        Command cmd = Command.Call.create(identifier);
        sendCommand(cmd, serverAddress);
        return true;
    }

    public void login(String identifier, SocketAddress remoteAddress) {
        this.database.identifier = identifier;
        this.identifier = identifier;
        this.serverAddress = remoteAddress;
        this.peer.connect(remoteAddress);
        sayHello(remoteAddress);
    }

    public List<Session> getSessions(String receiver) {
        List<Session> sessions = new ArrayList<>();
        LocationDelegate delegate = getDelegate();
        List<LocationValue> locations = delegate.getLocations(receiver);
        SocketAddress sourceAddress;
        SocketAddress mappedAddress;
        Connection conn;
        long now = (new Date()).getTime();
        for (LocationValue item : locations) {
            // source address
            sourceAddress = item.getSourceAddress();
            if (sourceAddress != null) {
                conn = peer.getConnection(sourceAddress);
                if (conn != null && conn.isConnected(now)) {
                    sessions.add(new Session(item, sourceAddress));
                    continue;
                }
            }
            // mapped address
            mappedAddress = item.getMappedAddress();
            if (mappedAddress != null) {
                conn = peer.getConnection(mappedAddress);
                if (conn != null && conn.isConnected(now)) {
                    sessions.add(new Session(item, mappedAddress));
                    continue;
                }
            }
        }
        return sessions;
    }

    //
    //  test
    //

    boolean sendText(String receiver, String text) {
        List<Session> sessions = getSessions(receiver);
        if (sessions.size() == 0) {
            System.out.printf("user (%s) not login ...\n", receiver);
            // ask the server to help building a connection
            call(receiver);
            return false;
        }
        long timestamp = (new Date()).getTime() / 1000;
        byte[] bytes = text.getBytes(Charset.forName("UTF-8"));
        Data content = new Data(bytes);
        Message msg = Message.create(identifier, receiver, timestamp, content, null, null);
        for (Session item : sessions) {
            System.out.printf("sending msg to %s:\n\t%s\n", item, msg);
            sendMessage(msg, item.address);
        }
        return true;
    }

    static final String CLIENT_IP = "192.168.31.64";
    static final int CLIENT_PORT = Data.random(1).getUInt8Value(0) + 9900;

    public static void main(String args[]) throws SocketException, InterruptedException {

        SocketAddress serverAddress = new InetSocketAddress(Server.SERVER_GZ1, Server.SERVER_PORT);
        System.out.printf("connecting to UDP server: %s ...\n", serverAddress);

        String user = "moky-" + CLIENT_PORT;
        String friend = "moky";

        Client client = new Client(CLIENT_IP, CLIENT_PORT);
        client.start();

        client.login(user, serverAddress);

        // test send
        String text = "你好 " + friend + "!";
        int index = 0;
        while (true) {
            Thread.sleep(5000);
            System.out.printf("---- [%d]\n", index);
            client.sendText(friend, text + " (" + index + ")");
            ++index;
        }
    }
}
