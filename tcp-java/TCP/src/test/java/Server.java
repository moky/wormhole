
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;

import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.startrek.PlainArrival;
import chat.dim.tcp.ServerHub;

public class Server implements Docker.Delegate {

    private final SocketAddress localAddress;

    private final TCPGate<ServerHub> gate;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        gate = new TCPGate<>(this, false);
        gate.setHub(new StreamServerHub(gate, true));
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
        getGate().send(data, localAddress, destination);
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Docker.Status previous, Docker.Status current,
                                SocketAddress remote, SocketAddress local, Connection conn,
                                Docker docker) {
        TCPGate.info("!!! connection (" + remote + ", " + local + ") state changed: " + previous + " -> " + current);
    }

    @Override
    public void onReceived(Arrival income, SocketAddress source, SocketAddress destination, Connection connection) {
        assert income instanceof PlainArrival : "arrival ship error: " + income;
        byte[] data = ((PlainArrival) income).getPackage();
        String text = new String(data, StandardCharsets.UTF_8);
        TCPGate.info("<<< received (" + data.length + " bytes) from " + source + ": " + text);
        text = (counter++) + "# " + data.length + " byte(s) received";
        data = text.getBytes(StandardCharsets.UTF_8);
        TCPGate.info(">>> responding: " + text);
        send(data, source);
    }
    static int counter = 0;

    @Override
    public void onSent(Departure outgo, SocketAddress source, SocketAddress destination, Connection connection) {
        // plain departure has no response,
        // we would not know whether the task is success here
    }

    @Override
    public void onError(Throwable error, Departure outgo, SocketAddress source, SocketAddress destination, Connection connection) {
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
