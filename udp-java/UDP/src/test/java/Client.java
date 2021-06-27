
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;

import chat.dim.net.BaseConnection;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.network.StarLink;

public class Client implements Connection.Delegate {

    private final BaseConnection connection;

    public Client(BaseConnection conn) {
        super();
        connection = conn;
    }

    @Override
    public void onConnectionStateChanged(Connection connection, ConnectionState oldStatus, ConnectionState newStatus) {
        info("!!! connection state changed: " + oldStatus + " -> " + newStatus);
    }

    public void onDataReceived(byte[] data, SocketAddress source, SocketAddress destination) {
        String text = new String(data, StandardCharsets.UTF_8);
        info("<<< received (" + data.length + " bytes) from " + source + " to " + destination + ": " + text);
    }

    public synchronized void start() {
        connection.start();
    }

    public int send(byte[] data) {
        return connection.send(data);
    }

    public byte[] receive() {
        return connection.receive();
    }

    public void close() {
        connection.close();
    }

    //
    //  Test
    //

    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }
    static void info(byte[] data) {
        info(new String(data, StandardCharsets.UTF_8));
    }

    public static void main(String[] args) throws InterruptedException {

        info("Connecting server (" + Server.HOST + ":" + Server.PORT + ") ...");

        StarLink conn = new StarLink(Server.HOST, Server.PORT);
        Client client = new Client(conn);
        conn.setDelegate(client);
        client.start();

        StringBuilder text = new StringBuilder();
        for (int index = 0; index < 1024; ++index) {
            text.append(" Hello!");
        }

        byte[] data;

        for (int index = 0; index < 16; ++index) {
            data = (index + " sheep:" + text).getBytes();
            info(">>> sending (" + data.length + " bytes): ");
            info(data);
            client.send(data);
            data = client.receive();
            if (data != null) {
                client.onDataReceived(data, null, null);
            }
            Thread.sleep(2000);
        }

        client.close();
    }
}
