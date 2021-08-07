
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.PackageConnection;
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

public class Client extends chat.dim.stun.Client implements Connection.Delegate {

    static final String CLIENT_IP = "192.168.0.111"; // Test
    static final int CLIENT_PORT = 9527;

    static SocketAddress SERVER_ADDRESS = new InetSocketAddress(Server.SERVER_IP, Server.SERVER_PORT);
//    static SocketAddress SERVER_ADDRESS = new InetSocketAddress(Server.SERVER_GZ1, Server.SERVER_PORT);
//    static SocketAddress SERVER_ADDRESS = new InetSocketAddress(Server.SERVER_HK2, Server.SERVER_PORT);

    static SocketAddress CLIENT_ADDRESS = new InetSocketAddress(CLIENT_IP, CLIENT_PORT);

    public final ActivePackageHub hub;

    public Client(String host, int port) {
        super(host, port);
        hub = new ClientHub(this);
    }

    @Override
    public void onConnectionStateChanging(Connection connection, ConnectionState current, ConnectionState next) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + current + " -> " + next);
        if (next.equals(ConnectionState.EXPIRED)) {
            try {
                heartbeat(connection);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
    private void heartbeat(Connection connection) throws IOException {
        assert connection instanceof PackageConnection : "connection error: " + connection;
        ((PackageConnection) connection).heartbeat(connection.getRemoteAddress());
    }

    @Override
    public void onConnectionReceivedData(Connection connection, SocketAddress remote, byte[] data) {
        if (data != null && data.length > 0) {
            chunks.add(data);
        }
    }

    private final List<byte[]> chunks = new ArrayList<>();

    @Override
    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        try {
            hub.sendMessage(data, source, destination);
            return 0;
        } catch (IOException e) {
            e.printStackTrace();
            return -1;
        }
    }

    @Override
    public byte[] receive() {
        byte[] data = null;
        long timeout = (new Date()).getTime() + 2000;
        while (true) {
            if (chunks.size() == 0) {
                // drive hub to receive data
                hub.tick();
            }
            if (chunks.size() > 0) {
                data = chunks.remove(0);
                break;
            }
            if (timeout < (new Date()).getTime()) {
                break;
            }
            Client.idle(256);
        }
        info("received " + (data == null ? 0 : data.length) + " bytes from " + SERVER_ADDRESS);
        return data;
    }

    @Override
    protected void info(String msg) {
        Date currentTime = new Date();
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String dateString = formatter.format(currentTime);
        System.out.printf("[%s] %s\n", dateString, msg);
    }

    static void idle(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public void detect(SocketAddress serverAddress) {
        info("----------------------------------------------------------------");
        info("-- Detection starts from : " + serverAddress);
        Map<String, Object> res = getNatType(serverAddress);
        info("-- Detection Result: " + res.get("NAT"));
        info("-- External Address: " + res.get("MAPPED-ADDRESS"));
        info("----------------------------------------------------------------");
    }

    public static void main(String[] args) {

        Client client = new Client(CLIENT_IP, CLIENT_PORT);
        client.detect(SERVER_ADDRESS);

        System.exit(0);
    }
}
