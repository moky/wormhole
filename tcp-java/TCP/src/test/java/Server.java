
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;

import chat.dim.net.Hub;
import chat.dim.port.Gate;
import chat.dim.startrek.PlainArrival;
import chat.dim.startrek.PlainDeparture;
import chat.dim.tcp.ServerHub;

public class Server implements Gate.Delegate<PlainDeparture, PlainArrival, Object> {

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
        gate.sendMessage(data, destination);
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        TCPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(PlainArrival ship, SocketAddress remote, Gate gate) {
        byte[] pack = ship.getData();
        String text = new String(pack, StandardCharsets.UTF_8);
        TCPGate.info("<<< received (" + pack.length + " bytes) from " + remote + ": " + text);
        text = (counter++) + "# " + pack.length + " byte(s) received";
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
        TCPGate.info(">>> responding: " + text);
        send(data, remote);
    }
    static int counter = 0;

    @Override
    public void onSent(PlainDeparture ship, SocketAddress remote, Gate gate) {
        int bodyLen = ship.getPackage().length;
        TCPGate.info("message sent: " + bodyLen + " byte(s) to " + remote);
    }

    @Override
    public void onError(Error error, PlainDeparture ship, SocketAddress remote, Gate gate) {
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
