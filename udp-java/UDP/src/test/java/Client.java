
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;

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

public class Client extends Thread implements Connection.Delegate {

    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }
    static void info(byte[] data) {
        info(new String(data, StandardCharsets.UTF_8));
    }

    static void idle(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
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
        String text = new String(data, StandardCharsets.UTF_8);
        info("<<< received (" + data.length + " bytes) from " + remote + ": " + text);
    }

    private void send(byte[] data, SocketAddress destination) {
        try {
            hub.sendMessage(data, null, destination);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    private void disconnect() {
        try {
            hub.disconnect(remoteAddress, null);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void run() {

        StringBuilder text = new StringBuilder();
        for (int index = 0; index < 1024; ++index) {
            text.append(" Hello!");
        }

        byte[] data;

        for (int index = 0; index < 16; ++index) {
            data = (index + " sheep:" + text).getBytes();
            info(">>> sending (" + data.length + " bytes): ");
            info(data);
            send(data, remoteAddress);
            idle(2000);
        }

        disconnect();
    }

    private static SocketAddress remoteAddress;
    private static ClientHub hub;

    public static void main(String[] args) {

        info("Connecting server (" + Server.HOST + ":" + Server.PORT + ") ...");

        remoteAddress = new InetSocketAddress(Server.HOST, Server.PORT);

        Client client = new Client();

        hub = new ClientHub(client);

        client.start();
    }
}
