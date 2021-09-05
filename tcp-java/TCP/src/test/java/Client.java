
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
import chat.dim.startrek.PlainDeparture;
import chat.dim.tcp.StreamChannel;

class ClientHub extends ActivePlainHub {

    public ClientHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        Channel channel = new StreamChannel(remote, local);
        channel.configureBlocking(false);
        return channel;
    }
}

public class Client implements Gate.Delegate {

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

    public void start() throws IOException {
        gate.hub.connect(remoteAddress, localAddress);
        gate.start();
    }

    void stop() {
        gate.stop();
    }

    private void send(byte[] data) {
        gate.sendMessage(data, remoteAddress);
    }

    //
    //  Gate Delegate
    //

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
        assert ship instanceof PlainDeparture;
        int bodyLen = ((PlainDeparture) ship).getPackage().length;
        TCPGate.info("message sent: " + bodyLen + " byte(s) to " + remote);
    }

    @Override
    public void onError(Error error, Departure ship, SocketAddress remote, Gate gate) {
        TCPGate.error(error.getMessage());
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

    public static void main(String[] args) throws IOException {

        SocketAddress local = new InetSocketAddress(Client.HOST, Client.PORT);
        SocketAddress remote = new InetSocketAddress(Server.HOST, Server.PORT);
        TCPGate.info("Connecting TCP server (" + local + "->" + remote + ") ...");

        Client client = new Client(local, remote);

        client.start();
        client.test();
        client.stop();
    }
}
