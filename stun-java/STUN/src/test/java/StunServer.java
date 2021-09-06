
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;

import chat.dim.net.Hub;
import chat.dim.port.Gate;
import chat.dim.startrek.PlainArrival;
import chat.dim.startrek.PlainDeparture;
import chat.dim.stun.Server;
import chat.dim.type.Data;
import chat.dim.udp.ServerHub;

public class StunServer extends Server implements Gate.Delegate<PlainDeparture, PlainArrival, Object> {

    private final UDPGate<ServerHub> gate;

    public StunServer(InetSocketAddress sourceAddress, int changePort,
                  InetSocketAddress changedAddress, InetSocketAddress neighbour) {
        super(sourceAddress, changePort, changedAddress, neighbour);
        gate = new UDPGate<>(this);
        gate.hub = new ServerHub(gate);
    }

    public void start() throws IOException {
        SocketAddress secondaryAddress = new InetSocketAddress(sourceAddress.getAddress(), changePort);
        gate.hub.bind(sourceAddress);
        gate.hub.bind(secondaryAddress);
        gate.start();

        UDPGate.info("STUN server started");
        UDPGate.info("source address: " + sourceAddress + ", another port: " + changePort + ", neighbour server: " + neighbour);
        UDPGate.info("changed address: " + changedAddress);
    }

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        UDPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(PlainArrival ship, SocketAddress source, SocketAddress destination, Gate gate) {
        byte[] pack = ship.getData();
        if (pack != null && pack.length > 0) {
            handle(new Data(pack), (InetSocketAddress) source);
        }
    }

    @Override
    public void onSent(PlainDeparture ship, SocketAddress source, SocketAddress destination, Gate gate) {
        int bodyLen = ship.getPackage().length;
        UDPGate.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onError(Error error, PlainDeparture ship, SocketAddress source, SocketAddress destination, Gate gate) {
        UDPGate.error(error.getMessage());
    }

    @Override
    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        try {
            gate.hub.connect(destination, source);
            gate.sendData(data, source, destination);
            return 0;
        } catch (IOException e) {
            e.printStackTrace();
            return -1;
        }
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

    public static void main(String[] args) throws IOException {

        InetSocketAddress primary = new InetSocketAddress(HOST, PORT);

        StunServer server = new StunServer(primary, CHANGE_PORT, CHANGED_ADDRESS, NEIGHBOUR_SERVER);

        server.start();
    }
}
