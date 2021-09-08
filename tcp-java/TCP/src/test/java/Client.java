
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.Random;

import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.startrek.PlainArrival;
import chat.dim.startrek.PlainDeparture;
import chat.dim.tcp.ClientHub;

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
        gate.connect(remoteAddress, localAddress);
        gate.start();
    }

    void stop() {
        gate.stop();
    }

    private void send(byte[] data) {
        gate.sendMessage(data, localAddress, remoteAddress);
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        TCPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(Arrival income, SocketAddress source, SocketAddress destination, Gate gate) {
        assert income instanceof PlainArrival : "arrival ship error: " + income;
        byte[] data = ((PlainArrival) income).getPackage();
        String text = new String(data, StandardCharsets.UTF_8);
        TCPGate.info("<<< received (" + data.length + " bytes) from " + source + ": " + text);
    }

    @Override
    public void onSent(Departure outgo, SocketAddress source, SocketAddress destination, Gate gate) {
        assert outgo instanceof PlainDeparture : "departure ship error: " + outgo;
        int bodyLen = ((PlainDeparture) outgo).getPackage().length;
        TCPGate.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onError(Error error, Departure outgo, SocketAddress source, SocketAddress destination, Gate gate) {
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

        TCPGate.idle(16000);
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
