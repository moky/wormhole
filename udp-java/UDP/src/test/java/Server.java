
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;

import chat.dim.mtp.Package;
import chat.dim.mtp.PackageArrival;
import chat.dim.mtp.PackageDeparture;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Docker;
import chat.dim.stargate.UDPGate;
import chat.dim.udp.ServerHub;

public class Server implements Docker.Delegate {

    private final SocketAddress localAddress;

    private final UDPGate<ServerHub> gate;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        gate = new UDPGate<>(this, false);
        gate.setHub(new PacketServerHub(gate));
    }

    private UDPGate<ServerHub> getGate() {
        return gate;
    }
    private ServerHub getHub() {
        return gate.getHub();
    }

    public void start() throws IOException {
        getHub().bind(localAddress);
        getGate().start();
    }

    private void send(byte[] data, SocketAddress destination) {
        getGate().sendCommand(data, localAddress, destination);
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

        text = (counter++) + "# " + payload.length + " byte(s) received";
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
        UDPGate.info(">>> responding: " + text);
        send(data, source);
    }
    static int counter = 0;

    @Override
    public void onDockerSent(Departure departure, Docker docker) {
        assert departure instanceof PackageDeparture : "departure ship error: " + departure;
        Package pack = ((PackageDeparture) departure).getPackage();
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
