
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;

import chat.dim.mtp.Package;
import chat.dim.mtp.PackageArrival;
import chat.dim.mtp.PackageDeparture;
import chat.dim.mtp.TransactionID;
import chat.dim.net.Hub;
import chat.dim.port.Gate;
import chat.dim.udp.ServerHub;

public class Server implements Gate.Delegate<PackageDeparture, PackageArrival, TransactionID> {

    private final SocketAddress localAddress;

    private final UDPGate<ServerHub> gate;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        gate = new UDPGate<>(this);
        gate.hub = new ServerHub(gate);
    }

    public void start() throws IOException {
        gate.hub.bind(localAddress);
        gate.start();
    }

    private void send(byte[] data, SocketAddress destination) {
        try {
            gate.hub.connect(destination, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
        gate.sendCommand(data, localAddress, destination);
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        UDPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(PackageArrival ship, SocketAddress source, SocketAddress destination, Gate gate) {
        Package pack = ship.getPackage();
        int headLen = pack.head.getSize();
        int bodyLen = pack.body.getSize();
        byte[] payload = pack.body.getBytes();
        String text = new String(payload, StandardCharsets.UTF_8);
        UDPGate.info("<<< received (" + headLen + " + " + bodyLen + " bytes) from " + source + ": " + text);
        text = (counter++) + "# " + payload.length + " byte(s) received";
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
        UDPGate.info(">>> responding: " + text);
        send(data, source);
    }
    static int counter = 0;

    @Override
    public void onSent(PackageDeparture ship, SocketAddress source, SocketAddress destination, Gate gate) {
        Package pack = ship.getPackage();
        int bodyLen = pack.head.bodyLength;
        if (bodyLen == -1) {
            bodyLen = pack.body.getSize();
        }
        UDPGate.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onError(Error error, PackageDeparture ship, SocketAddress source, SocketAddress destination, Gate gate) {
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
