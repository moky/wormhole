
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
import chat.dim.port.Docker;
import chat.dim.skywalker.Runner;
import chat.dim.stargate.UDPGate;
import chat.dim.udp.ClientHub;

public class Client implements Docker.Delegate {

    private final SocketAddress localAddress;
    private final SocketAddress remoteAddress;

    private final UDPGate<ClientHub> gate;

    Client(SocketAddress local, SocketAddress remote) {
        super();
        localAddress = local;
        remoteAddress = remote;
        gate = new UDPGate<>(this, true);
        gate.setHub(new PacketClientHub(gate));
    }

    private UDPGate<ClientHub> getGate() {
        return gate;
    }
    private ClientHub getHub() {
        return gate.getHub();
    }

    public void start() throws IOException {
        getHub().bind(localAddress);
        getGate().start();
    }

    void stop() {
        getGate().stop();
    }

    private void send(byte[] data) {
        getGate().sendMessage(data, localAddress, remoteAddress);
        getGate().sendCommand(data, localAddress, remoteAddress);
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onDockerStatusChanged(Docker.Status previous, Docker.Status current, Docker docker) {
        SocketAddress remote = docker.getRemoteAddress();
        SocketAddress local = docker.getLocalAddress();
        UDPGate.info("!!! connection (" + remote + ", " + local + ") state changed: " + previous + " -> " + current);
    }

    @Override
    public void onDockerReceived(Arrival income, Docker docker) {
        assert income instanceof PackageArrival : "arrival ship error: " + income;
        Package pack = ((PackageArrival) income).getPackage();
        int headLen = pack.head.getSize();
        int bodyLen = pack.body.getSize();
        byte[] payload = pack.body.getBytes();
        String text = new String(payload, StandardCharsets.UTF_8);
        SocketAddress source = docker.getRemoteAddress();
        UDPGate.info("<<< received (" + headLen + " + " + bodyLen + " bytes) from " + source + ": " + text);
    }

    @Override
    public void onDockerSent(Departure outgo, Docker docker) {
        assert outgo instanceof PackageDeparture : "departure ship error: " + outgo;
        Package pack = ((PackageDeparture) outgo).getPackage();
        int bodyLen = pack.head.bodyLength;
        if (bodyLen == -1) {
            bodyLen = pack.body.getSize();
        }
        SocketAddress destination = docker.getRemoteAddress();
        UDPGate.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onDockerFailed(Throwable error, Departure departure, Docker docker) {
        UDPGate.error(error.getMessage());
    }

    @Override
    public void onDockerError(Throwable error, Departure departure, Docker docker) {
        UDPGate.error(error.getMessage());
    }

    void test() {

        StringBuilder content = new StringBuilder();
        for (int index = 0; index < 1024; ++index) {
            content.append(" Hello!");
        }

        String text;
        byte[] data;
        Runner.idle(5000);

        for (int index = 0; index < 16; ++index) {
            text = index + " sheep:" + content;
            data = text.getBytes();
            UDPGate.info(">>> sending (" + data.length + " bytes): ");
            UDPGate.info(text);
            send(data);
            Runner.idle(2000);
        }

        Runner.idle(60000);
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

        UDPGate.info("Terminated.");
    }
}
