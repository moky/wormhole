
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
import chat.dim.dmtp.values.MappedAddressValue;
import chat.dim.dmtp.values.SourceAddressValue;
import chat.dim.mtp.task.Departure;
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
        SourceAddressValue sourceAddress;
        MappedAddressValue mappedAddress;
        SocketAddress address;
        Connection conn;
        for (LocationValue item : locations) {
            // source address
            sourceAddress = item.getSourceAddress();
            if (sourceAddress != null) {
                address = new InetSocketAddress(sourceAddress.ip, sourceAddress.port);
                conn = peer.getConnection(address);
                if (conn != null && conn.isConnected()) {
                    sessions.add(new Session(item, address));
                    continue;
                }
            }
            // mapped address
            mappedAddress = item.getMappedAddress();
            if (mappedAddress != null) {
                address = new InetSocketAddress(mappedAddress.ip, mappedAddress.port);
                conn = peer.getConnection(address);
                if (conn != null && conn.isConnected()) {
                    sessions.add(new Session(item, address));
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
        byte[] content = text.getBytes(Charset.forName("UTF-8"));
        Message msg = Message.create(identifier, receiver, timestamp, content, null, null);
        for (Session item : sessions) {
            System.out.printf("sending msg to:\n\t%s\n", item);
            sendMessage(msg, item.address);
        }
        return true;
    }

    public static void main(String args[]) throws SocketException, InterruptedException {

        SocketAddress serverAddress = new InetSocketAddress(Server.SERVER_GZ1, Server.SERVER_PORT);
        System.out.printf("connecting to UDP server: %s ...\n", serverAddress);

        Client client = new Client("192.168.31.64", 9527);
        client.start();

        client.login("moky", serverAddress);

        // test send
        String friend = "hulk";
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
