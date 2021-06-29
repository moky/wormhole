
import java.io.IOException;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.network.StarGate;

public class Server extends Thread implements Connection.Delegate {

//    static String HOST = "127.0.0.1";
    static String HOST = "192.168.31.91";
    static int PORT = 9394;

    private final StarGate connection;

    public Server(StarGate conn) {
        super();
        connection = conn;
    }

    @Override
    public void onConnectionStateChanged(Connection connection, ConnectionState oldStatus, ConnectionState newStatus) {
        info("connection state changed: " + oldStatus + " -> " + newStatus);
    }

    public void onDataReceived(byte[] data, SocketAddress source, SocketAddress destination) {
        String text = new String(data, StandardCharsets.UTF_8);
        info("received (" + data.length + " bytes) from " + source + " to " + destination + ": " + text);
        text = data.length + " byte(s) received";
        data = text.getBytes(StandardCharsets.UTF_8);
        send(data, source);
    }

    public int send(byte[] data, SocketAddress remote) {
        if (!connection.isOpen()) {
            return -1;
        }
        if (connection.isConnected()) {
            return connection.send(data);
        } else {
            return connection.send(data, remote);
        }
    }

    public StarGate.Cargo receive() {
        if (!connection.isOpen()) {
            return null;
        }
        if (connection.isConnected()) {
            byte[] data = connection.receive();
            if (data == null) {
                return null;
            }
            return new StarGate.Cargo(null, data);
        }
        StarGate.Cargo cargo = connection.recv();
        if (cargo == null) {
            return null;
        }
        try {
            connection.serverChannel.connect(cargo.source);
        } catch (IOException e) {
            e.printStackTrace();
        }
        return cargo;
    }

    @Override
    public synchronized void start() {
        connection.start();
        super.start();
    }

    @Override
    public void run() {
        StarGate.Cargo cargo;
        while (true) {
            cargo = receive();
            if (cargo != null) {
                onDataReceived(cargo.payload, cargo.source, null);
            } else {
                idle();
            }
        }
    }

    private void idle() {
        try {
            Thread.sleep(200);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    //
    //  Test
    //

    private static void info(String msg) {
        Client.info(msg);
    }
    private static void info(byte[] data) {
        Client.info(data);
    }

    public static void main(String[] args) throws IOException {

        info("Starting server (" + HOST + ":" + PORT + ") ...");

        StarGate conn = StarGate.create(HOST, PORT);
        Server server = new Server(conn);
        conn.setDelegate(server);
        server.start();
    }
}
