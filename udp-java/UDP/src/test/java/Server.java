
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.channels.DatagramChannel;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

import chat.dim.mtp.Package;
import chat.dim.mtp.PackageArrival;
import chat.dim.mtp.PackageDeparture;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.net.PackageHub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.udp.PackageChannel;

class ServerHub extends PackageHub {

    private final Map<SocketAddress, DatagramChannel> channels = new HashMap<>();

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    void bind(SocketAddress local) throws IOException {
        DatagramChannel sock = channels.get(local);
        if (sock == null) {
            sock = DatagramChannel.open();
            sock.socket().bind(local);
            sock.configureBlocking(false);
            channels.put(local, sock);
        }
        connect(null, local);
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        DatagramChannel sock = channels.get(local);
        if (sock == null) {
            throw new SocketException("failed to get channel: " + remote + " -> " + local);
        } else {
            Channel channel = new PackageChannel(sock);
            channel.configureBlocking(false);
            return channel;
        }
    }
}

public class Server implements Gate.Delegate {

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
        gate.sendCommand(data, destination);
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        UDPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(Arrival ship, SocketAddress remote, Gate gate) {
        assert ship instanceof PackageArrival : "income ship error: " + ship;
        Package pack = ((PackageArrival) ship).getPackage();
        int headLen = pack.head.getSize();
        int bodyLen = pack.body.getSize();
        byte[] payload = pack.body.getBytes();
        String text = new String(payload, StandardCharsets.UTF_8);
        UDPGate.info("<<< received (" + headLen + " + " + bodyLen + " bytes) from " + remote + ": " + text);
        text = (counter++) + "# " + payload.length + " byte(s) received";
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
        UDPGate.info(">>> responding: " + text);
        send(data, remote);
    }
    static int counter = 0;

    @Override
    public void onSent(Departure ship, SocketAddress remote, Gate gate) {
        assert ship instanceof PackageDeparture;
        int bodyLen = ((PackageDeparture) ship).bodyLength;
        UDPGate.info("message sent: " + bodyLen + " byte(s) to " + remote);
    }

    @Override
    public void onError(Error error, Departure ship, SocketAddress remote, Gate gate) {
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
