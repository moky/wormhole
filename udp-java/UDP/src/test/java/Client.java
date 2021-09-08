
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.Random;

import chat.dim.mtp.Package;
import chat.dim.mtp.PackageArrival;
import chat.dim.mtp.PackageDeparture;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.udp.ClientHub;

public class Client implements Gate.Delegate {

    private final SocketAddress localAddress;
    private final SocketAddress remoteAddress;

    private final UDPGate<ClientHub> gate;

    Client(SocketAddress local, SocketAddress remote) {
        super();
        localAddress = local;
        remoteAddress = remote;
        gate = new UDPGate<>(this);
        gate.hub = new ClientHub(gate);
    }

    public void start() throws IOException {
        gate.hub.bind(localAddress);
        gate.connect(remoteAddress, localAddress);
        gate.start();
    }

    void stop() {
        gate.stop();
    }

    private void send(byte[] data) {
        gate.sendCommand(data, localAddress, remoteAddress);
        gate.sendMessage(data, localAddress, remoteAddress);
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        UDPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(Arrival income, SocketAddress source, SocketAddress destination, Gate gate) {
        assert income instanceof PackageArrival : "arrival ship error: " + income;
        Package pack = ((PackageArrival) income).getPackage();
        int headLen = pack.head.getSize();
        int bodyLen = pack.body.getSize();
        byte[] payload = pack.body.getBytes();
        String text = new String(payload, StandardCharsets.UTF_8);
        UDPGate.info("<<< received (" + headLen + " + " + bodyLen + " bytes) from " + source + ": " + text);
    }

    @Override
    public void onSent(Departure outgo, SocketAddress source, SocketAddress destination, Gate gate) {
        assert outgo instanceof PackageDeparture : "departure ship error: " + outgo;
        Package pack = ((PackageDeparture) outgo).getPackage();
        int bodyLen = pack.head.bodyLength;
        if (bodyLen == -1) {
            bodyLen = pack.body.getSize();
        }
        UDPGate.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onError(Error error, Departure outgo, SocketAddress source, SocketAddress destination, Gate gate) {
        UDPGate.error(error.getMessage());
    }

    void test() {

        StringBuilder text = new StringBuilder();
        for (int index = 0; index < 1024; ++index) {
            text.append(" Hello!");
        }

        byte[] data;

        for (int index = 0; index < 16; ++index) {
            data = (index + " sheep:" + text).getBytes();
            UDPGate.info(">>> sending (" + data.length + " bytes): ");
            UDPGate.info(data);
            send(data);
            UDPGate.idle(2000);
        }

        UDPGate.idle(5000);
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
        UDPGate.info("Connecting UDP server (" + local + " -> " + remote + ") ...");

        Client client = new Client(local, remote);

        client.start();
        client.test();
        client.stop();
    }
}
