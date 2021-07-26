
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.tcp.ActiveStreamHub;

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
        byte[] data = {'P', 'I', 'N', 'G'};
        send(data, connection.getLocalAddress(), connection.getRemoteAddress());
    }

    public void onDataReceived(byte[] data, SocketAddress source, SocketAddress destination) {
        String text = new String(data, StandardCharsets.UTF_8);
        info("<<< received (" + data.length + " bytes) from " + source + " to " + destination + ": " + text);
    }

    private byte[] receive(SocketAddress source, SocketAddress destination) {
        try {
            return hub.receive(source, destination);
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        }
    }
    private boolean send(byte[] data, SocketAddress source, SocketAddress destination) {
        try {
            return hub.send(data, source, destination);
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
    }
    private void disconnect(SocketAddress remote, SocketAddress local) {
        try {
            hub.disconnect(remote, local);
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
            send(data, null, remoteAddress);
            idle(2000);
            data = receive(remoteAddress, null);
            if (data != null) {
                onDataReceived(data, remoteAddress, null);
            }
        }

        disconnect(remoteAddress, null);
    }

    private static SocketAddress remoteAddress;
    private static Hub hub;

    public static void main(String[] args) {

        info("Connecting server (" + Server.HOST + ":" + Server.PORT + ") ...");

        remoteAddress = new InetSocketAddress(Server.HOST, Server.PORT);

        Client client = new Client();
        hub = new ActiveStreamHub(client);
        client.start();
    }
}
