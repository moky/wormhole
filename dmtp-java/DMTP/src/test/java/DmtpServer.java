
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
import chat.dim.mtp.TransactionID;
import chat.dim.net.Hub;
import chat.dim.port.Gate;
import chat.dim.udp.ServerHub;

public class DmtpServer extends Server implements Gate.Delegate<PackageDeparture, PackageArrival, TransactionID> {

    private final SocketAddress localAddress;

    private final UDPGate<ServerHub> gate;

    public DmtpServer(SocketAddress local) {
        super();
        localAddress = local;
        gate = new UDPGate<>(this);
        gate.hub = new ServerHub(gate);
    }

    @Override
    protected void connect(SocketAddress remote) {
        try {
            gate.connect(remote, localAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void start() throws IOException {
        gate.hub.bind(localAddress);
        gate.start();
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
        onReceivedPackage(source, pack);
    }

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

    @Override
    public boolean sendMessage(Message msg, SocketAddress destination) {
        gate.sendMessage(msg.getBytes(), localAddress, destination);
        return true;
    }

    @Override
    public boolean sendCommand(Command cmd, SocketAddress destination) {
        gate.sendCommand(cmd.getBytes(), localAddress, destination);
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
        database = new ContactManager(server.gate.hub, server.localAddress);
        database.identifier = "station@anywhere";
        server.setDelegate(database);

        server.start();
    }
}
