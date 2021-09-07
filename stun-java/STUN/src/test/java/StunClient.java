
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

import chat.dim.net.Hub;
import chat.dim.port.Gate;
import chat.dim.startrek.PlainArrival;
import chat.dim.startrek.PlainDeparture;
import chat.dim.stun.Client;
import chat.dim.udp.ClientHub;

public class StunClient extends Client implements Gate.Delegate<PlainDeparture, PlainArrival, Object> {

    private SocketAddress remoteAddress = null;

    private final UDPGate<ClientHub> gate;

    StunClient(InetSocketAddress local) {
        super(local);
        gate = new UDPGate<>(this);
        gate.hub = new ClientHub(gate);
    }

    public void start() throws IOException {
        gate.hub.bind(sourceAddress);
        gate.start();
    }

    void stop() {
        gate.stop();
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        UDPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(PlainArrival ship, SocketAddress source, SocketAddress destination, Gate gate) {
        byte[] pack = ship.getData();
        if (pack != null && pack.length > 0) {
            chunks.add(pack);
        }
    }
    private final List<byte[]> chunks = new ArrayList<>();

    @Override
    public void onSent(PlainDeparture ship, SocketAddress source, SocketAddress destination, Gate gate) {
        byte[] pack = ship.getPackage();
        int bodyLen = pack.length;
        UDPGate.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onError(Error error, PlainDeparture ship, SocketAddress source, SocketAddress destination, Gate gate) {
        UDPGate.error(error.getMessage());
    }

    @Override
    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        gate.sendData(data, source, destination);
        return 0;
    }

    @Override
    public byte[] receive() {
        byte[] data = null;
        long timeout = (new Date()).getTime() + 2000;
        while (true) {
            if (chunks.size() > 0) {
                data = chunks.remove(0);
                break;
            }
            if (timeout < (new Date()).getTime()) {
                break;
            }
            UDPGate.idle(256);
        }
        info("received " + (data == null ? 0 : data.length) + " bytes from " + remoteAddress);
        return data;
    }

    @Override
    protected void info(String msg) {
        UDPGate.info(msg);
    }

    public void detect(SocketAddress serverAddress) throws IOException {
        remoteAddress = serverAddress;
        gate.connect(remoteAddress, sourceAddress);
        info("----------------------------------------------------------------");
        info("-- Detection starts from : " + serverAddress);
        Map<String, Object> res = getNatType(serverAddress);
        info("-- Detection Result: " + res.get("NAT"));
        info("-- External Address: " + res.get("MAPPED-ADDRESS"));
        info("----------------------------------------------------------------");
    }

    static String HOST;
    static final int PORT = 9527;

    static {
        try {
            HOST = Hub.getLocalAddressString();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) throws IOException {

        InetSocketAddress a1 = new InetSocketAddress("stun.xten.com", 3478);
        //remoteAddress = new InetSocketAddress("stun.voipbuster.com", 3478);
        //remoteAddress = new InetSocketAddress("stun.sipgate.net", 3478);
        //remoteAddress = new InetSocketAddress("stun.ekiga.net", 3478);
        //remoteAddress = new InetSocketAddress("stun.schlund.de", 3478);
        //remoteAddress = new InetSocketAddress("stun.voipstunt.com", 3478);  // Full Cone NAT?
        //remoteAddress = new InetSocketAddress("stun.counterpath.com", 3478);
        //remoteAddress = new InetSocketAddress("stun.1und1.de", 3478);
        //remoteAddress = new InetSocketAddress("stun.gmx.net", 3478);
        //remoteAddress = new InetSocketAddress("stun.callwithus.com", 3478);
        //remoteAddress = new InetSocketAddress("stun.counterpath.net", 3478);
        //remoteAddress = new InetSocketAddress("stun.internetcalls.com", 3478);

        System.out.printf("connecting to STUN server: (%s:%d) ...\n", StunServer.HOST, StunServer.PORT);

        InetSocketAddress local = new InetSocketAddress(HOST, PORT);
        InetSocketAddress remote = new InetSocketAddress(StunServer.HOST, StunServer.PORT);
        StunClient client = new StunClient(local);

        client.start();
        client.detect(a1);
        client.detect(remote);
        client.stop();
    }
}
