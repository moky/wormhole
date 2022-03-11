
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.Random;

import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.skywalker.Runner;
import chat.dim.stargate.TCPGate;
import chat.dim.startrek.PlainArrival;
import chat.dim.tcp.ClientHub;

public class Client implements Docker.Delegate {

    private final SocketAddress localAddress;
    private final SocketAddress remoteAddress;

    private final TCPGate<ClientHub> gate;

    Client(SocketAddress local, SocketAddress remote) {
        super();
        localAddress = local;
        remoteAddress = remote;
        gate = new TCPGate<>(this, true);
        gate.setHub(new StreamClientHub(gate));
    }

    private TCPGate<ClientHub> getGate() {
        return gate;
    }

    public void start() {
        getGate().start();
    }

    void stop() {
        getGate().stop();
    }

    private void send(byte[] data) {
        getGate().send(data, localAddress, remoteAddress);
    }

    //
    //  Gate Delegate
    //

    public void onDockerStatusChanged(Docker.Status previous, Docker.Status current, Docker docker) {
        SocketAddress remote = docker.getRemoteAddress();
        SocketAddress local = docker.getLocalAddress();
        TCPGate.info("!!! connection (" + remote + ", " + local + ") state changed: " + previous + " -> " + current);
    }

    @Override
    public void onDockerReceived(Arrival income, Docker docker) {
        assert income instanceof PlainArrival : "arrival ship error: " + income;
        byte[] data = ((PlainArrival) income).getPackage();
        String text = new String(data, StandardCharsets.UTF_8);
        SocketAddress source = docker.getRemoteAddress();
        TCPGate.info("<<< received (" + data.length + " bytes) from " + source + ": " + text);
    }

    @Override
    public void onDockerSent(Departure departure, Docker docker) {
        // plain departure has no response,
        // we would not know whether the task is success here
    }

    @Override
    public void onDockerFailed(Throwable error, Departure departure, Docker docker) {
        TCPGate.error(error.getMessage());
    }

    void test() {

        StringBuilder content = new StringBuilder();
        for (int index = 0; index < 1024; ++index) {
            content.append(" Hello!");
        }

        String text;
        byte[] data;

        for (int index = 0; index < 16; ++index) {
            text = index + " sheep:" + content;
            data = text.getBytes();
            TCPGate.info(">>> sending (" + data.length + " bytes): ");
            TCPGate.info(text);
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

    public static void main(String[] args) {

        SocketAddress local = new InetSocketAddress(Client.HOST, Client.PORT);
        SocketAddress remote = new InetSocketAddress(Server.HOST, Server.PORT);
        TCPGate.info("Connecting TCP server (" + local + "->" + remote + ") ...");

        Client client = new Client(local, remote);

        client.start();
        client.test();
        client.stop();

        TCPGate.info("Terminated.");
    }
}
