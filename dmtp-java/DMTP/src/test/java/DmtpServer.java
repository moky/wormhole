
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;

import chat.dim.dmtp.ContactManager;
import chat.dim.dmtp.Server;
import chat.dim.dmtp.protocol.Command;
import chat.dim.dmtp.protocol.Message;
import chat.dim.mtp.Package;
import chat.dim.mtp.PackageArrival;
import chat.dim.mtp.PackageDeparture;
import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.udp.ServerHub;

public class DmtpServer extends Server implements Gate.Delegate {

    private final SocketAddress localAddress;

    private final UDPGate<ServerHub> gate;

    public DmtpServer(SocketAddress local) {
        super();
        localAddress = local;
        gate = new UDPGate<>(this);
        gate.setHub(new ServerHub(gate));
    }

    private UDPGate<ServerHub> getGate() {
        return gate;
    }
    private ServerHub getHub() {
        return gate.getHub();
    }

    private void bind(SocketAddress local) throws IOException {
        getHub().bind(local);
    }
    private Connection connect(SocketAddress remote, SocketAddress local) {
        return getHub().connect(remote, local);
    }

    @Override
    protected void connect(SocketAddress remote) {
        connect(remote, localAddress);
    }

    public void start() throws IOException {
        bind(localAddress);
        getGate().start();
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
        onReceivedPackage(source, pack);
    }

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

    @Override
    public boolean sendMessage(Message msg, SocketAddress destination) {
        getGate().sendMessage(msg.getBytes(), localAddress, destination);
        return true;
    }

    @Override
    public boolean sendCommand(Command cmd, SocketAddress destination) {
        getGate().sendCommand(cmd.getBytes(), localAddress, destination);
        return true;
    }

    @Override
    public boolean processCommand(Command cmd, SocketAddress source) {
        UDPGate.info("received cmd from " + source + ": " + cmd);
        return super.processCommand(cmd, source);
    }

    @Override
    public boolean processMessage(Message msg, SocketAddress source) {
        UDPGate.info("received msg from " + source + ": " + msg);
        return true;
    }

    static String HOST;
    static int PORT = 9395;

    static {
        try {
            HOST = Hub.getLocalAddressString();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    static ContactManager database;
    static DmtpServer server;

    public static void main(String[] args) throws IOException {

        SocketAddress local = new InetSocketAddress(HOST, PORT);
        UDPGate.info("Starting DMTP server (" + local + ") ...");

        server = new DmtpServer(local);

        // database for location of contacts
        database = new ContactManager(server.getHub(), server.localAddress);
        database.identifier = "station@anywhere";
        server.setDelegate(database);

        server.start();
    }
}
