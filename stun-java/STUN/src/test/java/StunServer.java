
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;

import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.startrek.PlainArrival;
import chat.dim.startrek.PlainDeparture;
import chat.dim.stun.Server;
import chat.dim.type.Data;
import chat.dim.udp.PackageHub;

public class StunServer extends Server implements Gate.Delegate {

    private final UDPGate<PackageHub> gate;

    public StunServer(InetSocketAddress sourceAddress, int changePort,
                  InetSocketAddress changedAddress, InetSocketAddress neighbour) {
        super(sourceAddress, changePort, changedAddress, neighbour);
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
        SocketAddress secondaryAddress = new InetSocketAddress(sourceAddress.getAddress(), changePort);
        getHub().bind(sourceAddress);
        getHub().bind(secondaryAddress);
        getGate().start();

        info("STUN server started");
        info("source address: " + sourceAddress + ", another port: " + changePort + ", neighbour server: " + neighbour);
        info("changed address: " + changedAddress);
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, SocketAddress local, Gate gate) {
        info("!!! connection (" + remote + ", " + local + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(Arrival income, SocketAddress source, SocketAddress destination, Connection connection) {
        assert income instanceof PlainArrival : "arrival ship error: " + income;
        byte[] data = ((PlainArrival) income).getPackage();
        if (data != null && data.length > 0) {
            handle(new Data(data), (InetSocketAddress) source);
        }
    }

    @Override
    public void onSent(Departure outgo, SocketAddress source, SocketAddress destination, Connection connection) {
        assert outgo instanceof PlainDeparture : "departure ship error: " + outgo;
        int bodyLen = ((PlainDeparture) outgo).getPackage().length;
        info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onError(Throwable error, Departure outgo, SocketAddress source, SocketAddress destination, Connection connection) {
        UDPGate.error(error.getMessage());
    }

    @Override
    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        getGate().sendData(data, source, destination);
        return 0;
    }

    @Override
    protected void info(String msg) {
        UDPGate.info(msg);
    }

    static String HOST;
    static int PORT = 3478;

    static {
        try {
            HOST = Hub.getLocalAddressString();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    static int CHANGE_PORT = 3479;

    static final String SERVER_GZ1 = "134.175.87.98"; // GZ-1
    static final String SERVER_HK2 = "129.226.128.17"; // HK-2

    static final InetSocketAddress CHANGED_ADDRESS = new InetSocketAddress(SERVER_HK2, 3478);
    static final InetSocketAddress NEIGHBOUR_SERVER = new InetSocketAddress(SERVER_HK2, 3478);

    static StunServer server;

    public static void main(String[] args) throws IOException {

        InetSocketAddress primary = new InetSocketAddress(HOST, PORT);

        server = new StunServer(primary, CHANGE_PORT, CHANGED_ADDRESS, NEIGHBOUR_SERVER);

        server.start();
    }
}
