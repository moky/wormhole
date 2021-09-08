
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;

import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.startrek.PlainArrival;
import chat.dim.startrek.PlainDeparture;
import chat.dim.tcp.ServerHub;

public class Server implements Gate.Delegate {

    private final SocketAddress localAddress;

    private final TCPGate<ServerHub> gate;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        gate = new TCPGate<>(this);
        gate.hub = new ServerHub(gate);
    }

    public void start() throws IOException {
        gate.hub.bind(localAddress);
        gate.hub.start();
        gate.start();
    }

    private void send(byte[] data, SocketAddress destination) {
        gate.sendMessage(data, localAddress, destination);
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
        text = (counter++) + "# " + data.length + " byte(s) received";
        data = text.getBytes(StandardCharsets.UTF_8);
        TCPGate.info(">>> responding: " + text);
        send(data, source);
    }
    static int counter = 0;

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
