
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;

import chat.dim.mtp.Package;
import chat.dim.mtp.PackageArrival;
import chat.dim.mtp.PackageDeparture;
import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.udp.PackageHub;

public class Server implements Gate.Delegate {

    private final SocketAddress localAddress;

    private final UDPGate<PackageHub> gate;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        gate = new UDPGate<>(this);
        gate.setHub(new PackageHub(gate));
    }

    private UDPGate<PackageHub> getGate() {
        return gate;
    }
    private PackageHub getHub() {
        return gate.getHub();
    }

    public void start() throws IOException {
        getHub().bind(localAddress);
        getGate().start();
    }

    private void send(byte[] data, SocketAddress destination) throws IOException {
        getGate().sendCommand(data, localAddress, destination);
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, SocketAddress local, Gate gate) {
        UDPGate.info("!!! connection (" + remote + ", " + local + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(Arrival income, SocketAddress source, SocketAddress destination, Connection connection) {
        assert income instanceof PackageArrival : "arrival ship error: " + income;
        Package pack = ((PackageArrival) income).getPackage();
        int headLen = pack.head.getSize();
        int bodyLen = pack.body.getSize();
        byte[] payload = pack.body.getBytes();
        String text = new String(payload, StandardCharsets.UTF_8);
        UDPGate.info("<<< received (" + headLen + " + " + bodyLen + " bytes) from " + source + ": " + text);

        text = (counter++) + "# " + payload.length + " byte(s) received";
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
        UDPGate.info(">>> responding: " + text);
        try {
            send(data, source);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    static int counter = 0;

    @Override
    public void onSent(Departure outgo, SocketAddress source, SocketAddress destination, Connection connection) {
        assert outgo instanceof PackageDeparture : "departure ship error: " + outgo;
        Package pack = ((PackageDeparture) outgo).getPackage();
        int bodyLen = pack.head.bodyLength;
        if (bodyLen == -1) {
            bodyLen = pack.body.getSize();
        }
        UDPGate.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onError(Throwable error, Departure outgo, SocketAddress source, SocketAddress destination, Connection connection) {
        UDPGate.error(error.getMessage());
    }

    static String HOST;
    static int PORT = 9394;

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
        UDPGate.info("Starting UDP server (" + local + ") ...");

        server = new Server(local);

        server.start();
    }
}
