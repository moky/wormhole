
import java.io.IOError;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;

import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.stargate.TCPGate;
import chat.dim.startrek.PlainArrival;
import chat.dim.tcp.ServerHub;

public class Server implements Docker.Delegate {

    private final SocketAddress localAddress;

    private final TCPGate<ServerHub> gate;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        gate = new TCPGate<>(this, false);
        gate.setHub(new StreamServerHub(gate));
    }

    private TCPGate<ServerHub> getGate() {
        return gate;
    }
    private ServerHub getHub() {
        return gate.getHub();
    }

    public void start() throws IOException {
        getHub().bind(localAddress);
        getHub().start();
        getGate().start();
    }

    private void send(byte[] data, SocketAddress destination) {
        boolean ok = getGate().sendMessage(data, destination, localAddress);
        assert ok;
    }

    //
    //  Gate Delegate
    //

    @Override
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
        text = (counter++) + "# " + data.length + " byte(s) received";
        data = text.getBytes(StandardCharsets.UTF_8);
        TCPGate.info(">>> responding: " + text);
        send(data, source);
    }
    static int counter = 0;

    @Override
    public void onDockerSent(Departure departure, Docker docker) {
        // plain departure has no response,
        // we would not know whether the task is success here
    }

    @Override
    public void onDockerFailed(IOError error, Departure departure, Docker docker) {
        TCPGate.error(error.getMessage());
    }

    @Override
    public void onDockerError(IOError error, Departure departure, Docker docker) {
        TCPGate.error(error.getMessage());
    }

    static String HOST;
    static final int PORT = 9394;

    static {
        try {
            HOST = Hub.getLocalAddressString();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    static Server server;

    public static void main(String[] args) throws IOException {

        SocketAddress local = new InetSocketAddress(HOST, PORT);
        TCPGate.info("Starting TCP server (" + local + ") ...");

        server = new Server(local);

        server.start();
    }
}
