
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.Random;

import chat.dim.net.ActiveRawDataHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.tcp.StreamChannel;

class ClientHub extends ActiveRawDataHub {

    private boolean running = false;

    public ClientHub(Connection.Delegate<byte[]> delegate) {
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
        Channel channel = new StreamChannel(remote, local);
        channel.configureBlocking(false);
        return channel;
    }
}

public class Client implements Runnable, Connection.Delegate<byte[]> {

    private final SocketAddress localAddress;
    private final SocketAddress remoteAddress;
    private final ClientHub hub;

    Client(SocketAddress local, SocketAddress remote) {
        super();
        localAddress = local;
        remoteAddress = remote;
        hub = new ClientHub(this);
    }

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
    public void onConnectionStateChanged(Connection<byte[]> connection, ConnectionState previous, ConnectionState current) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + previous + " -> " + current);
    }

    @Override
    public void onConnectionDataReceived(Connection<byte[]> connection, SocketAddress remote, byte[] pack) {
        String text = new String(pack, StandardCharsets.UTF_8);
        info("<<< received (" + pack.length + " bytes) from " + remote + ": " + text);
    }

    private void send(byte[] data) {
        try {
            hub.send(data, localAddress, remoteAddress);
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

    void test() {

        StringBuilder text = new StringBuilder();
        for (int index = 0; index < 1024; ++index) {
            text.append(" Hello!");
        }

        byte[] data;

        for (int index = 0; index < 16; ++index) {
            data = (index + " sheep:" + text).getBytes();
            info(">>> sending (" + data.length + " bytes): ");
            info(data);
            send(data);
            idle(2000);
        }
    }

    static String HOST;
    static int PORT;

    static {
        try {
            HOST = Hub.getLocalAddressString();
            Random random = new Random();
            PORT = 9900 + random.nextInt(100);
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {

        SocketAddress local = new InetSocketAddress(Client.HOST, Client.PORT);
        SocketAddress remote = new InetSocketAddress(Server.HOST, Server.PORT);
        info("Connecting TCP server (" + local + "->" + remote + ") ...");

        Client client = new Client(local, remote);

        client.start();
        client.test();
        client.stop();
    }
}
