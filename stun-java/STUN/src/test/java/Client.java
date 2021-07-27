
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Map;

import chat.dim.mtp.DataType;
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

public class Client extends chat.dim.stun.Client implements Connection.Delegate {

    static final String CLIENT_IP = "192.168.0.108"; // Test
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
            assert connection instanceof PackageConnection : "connection error: " + connection;
            ((PackageConnection) connection).heartbeat(connection.getRemoteAddress());
        }
    }

    @Override
    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        Package pack = Package.create(DataType.Message, new Data(data));
        try {
            return hub.sendPackage(pack, source, destination) ? 0 : -1;
        } catch (IOException e) {
            e.printStackTrace();
            return -1;
        }
    }

    private byte[] receive(SocketAddress source, SocketAddress destination) {
        try {
            Package pack = hub.receivePackage(source, destination);
            if (pack != null) {
                return pack.body.getBytes();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }

    @Override
    public byte[] receive() {
        byte[] data;
        long timeout = (new Date()).getTime() + 2000;
        while (true) {
            data = receive(SERVER_ADDRESS, CLIENT_ADDRESS);
            if (data != null) {
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
