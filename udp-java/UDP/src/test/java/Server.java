
import java.io.IOError;
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
import chat.dim.port.Porter;
import chat.dim.stargate.UDPGate;
import chat.dim.udp.ServerHub;
import chat.dim.utils.Log;

public class Server implements Porter.Delegate {

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
        boolean ok = getGate().sendCommand(data, destination, localAddress);
        assert ok;
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onPorterStatusChanged(Porter.Status previous, Porter.Status current, Porter docker) {
        SocketAddress remote = docker.getRemoteAddress();
        SocketAddress local = docker.getLocalAddress();
        Log.info("!!! connection (" + remote + ", " + local + ") state changed: " + previous + " -> " + current);
    }

    @Override
    public void onPorterReceived(Arrival income, Porter docker) {
        assert income instanceof PackageArrival : "arrival ship error: " + income;
        Package pack = ((PackageArrival) income).getPackage();
        int headLen = pack.head.getSize();
        int bodyLen = pack.body.getSize();
        byte[] payload = pack.body.getBytes();
        String text = new String(payload, StandardCharsets.UTF_8);
        SocketAddress source = docker.getRemoteAddress();
        Log.info("<<< received (" + headLen + " + " + bodyLen + " bytes) from " + source + ": " + text);

        text = (counter++) + "# " + payload.length + " byte(s) received";
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
        Log.info(">>> responding: " + text);
        send(data, source);
    }
    static int counter = 0;

    @Override
    public void onPorterSent(Departure departure, Porter docker) {
        assert departure instanceof PackageDeparture : "departure ship error: " + departure;
        Package pack = ((PackageDeparture) departure).getPackage();
        int bodyLen = pack.head.bodyLength;
        if (bodyLen == -1) {
            bodyLen = pack.body.getSize();
        }
        SocketAddress destination = docker.getRemoteAddress();
        Log.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onPorterFailed(IOError error, Departure departure, Porter docker) {
        Log.error(error.getMessage());
    }

    @Override
    public void onPorterError(IOError error, Departure departure, Porter docker) {
        Log.error(error.getMessage());
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
        Log.info("Starting UDP server (" + local + ") ...");

        server = new Server(local);

        server.start();
    }
}
