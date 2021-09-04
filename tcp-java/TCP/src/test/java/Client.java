
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.Random;

import chat.dim.net.ActivePlainHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.startrek.PlainArrival;
import chat.dim.tcp.StreamChannel;

class ClientHub extends ActivePlainHub {

    private boolean running = false;

    public ClientHub(Connection.Delegate delegate) {
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

public class Client implements Runnable, Gate.Delegate {

    private final SocketAddress localAddress;
    private final SocketAddress remoteAddress;

    private final TCPGate<ClientHub> gate;

    Client(SocketAddress local, SocketAddress remote) {
        super();
        localAddress = local;
        remoteAddress = remote;
        gate = new TCPGate<>(this);
        gate.hub = new ClientHub(gate);
    }

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        TCPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(Arrival ship, SocketAddress remote, Gate gate) {
        assert ship instanceof PlainArrival : "income ship error: " + ship;
        byte[] pack = ((PlainArrival) ship).getData();
        String text = new String(pack, StandardCharsets.UTF_8);
        TCPGate.info("<<< received (" + pack.length + " bytes) from " + remote + ": " + text);
    }

    @Override
    public void onSent(Departure ship, SocketAddress remote, Gate gate) {

    }

    @Override
    public void onError(Error error, Departure ship, SocketAddress remote, Gate gate) {

    }

    private void send(byte[] data) {
        boolean ok = gate.send(data, remoteAddress);
        assert ok;
    }

    public void start() {
        try {
            gate.hub.connect(remoteAddress, localAddress);
            gate.hub.start();
        } catch (IOException e) {
            e.printStackTrace();
        }
        new Thread(this).start();
    }

    void stop() {
        gate.hub.stop();
    }

    @Override
    public void run() {
        while (gate.hub.isRunning()) {
            gate.hub.tick();
            if (gate.hub.getActivatedCount() == 0) {
                TCPGate.idle(8);
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
            TCPGate.info(">>> sending (" + data.length + " bytes): ");
            TCPGate.info(data);
            send(data);
            TCPGate.idle(2000);
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
        TCPGate.info("Connecting TCP server (" + local + "->" + remote + ") ...");

        Client client = new Client(local, remote);

        client.start();
        client.test();
        client.stop();
    }
}
