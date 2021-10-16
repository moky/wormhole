
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Random;

import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.skywalker.Runner;
import chat.dim.startrek.PlainArrival;
import chat.dim.startrek.PlainDeparture;
import chat.dim.stun.Client;
import chat.dim.udp.ClientHub;

public class StunClient extends Client implements Gate.Delegate {

    private final UDPGate<ClientHub> gate;

    StunClient(InetSocketAddress local) {
        super(local);
        gate = new UDPGate<>(this);
        gate.setHub(new ClientHub(gate));
    }

    private UDPGate<ClientHub> getGate() {
        return gate;
    }
    private ClientHub getHub() {
        return gate.getHub();
    }

    public void start() throws IOException {
        getHub().bind(sourceAddress);
        getGate().start();
    }

    void stop() {
        getGate().stop();
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
            chunks.add(data);
        }
    }
    private final List<byte[]> chunks = new ArrayList<>();

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
    public byte[] receive() {
        byte[] data = null;
        long timeout = (new Date()).getTime() + 2000;
        while (true) {
            if (chunks.size() > 0) {
                data = chunks.remove(0);
                break;
            } else if (timeout < (new Date()).getTime()) {
                // timeout
                break;
            } else {
                Runner.idle(256);
            }
        }
        info("received " + (data == null ? 0 : data.length) + " bytes");
        return data;
    }

    @Override
    protected void info(String msg) {
        UDPGate.info(msg);
    }

    public void detect(SocketAddress serverAddress) {
        info("----------------------------------------------------------------");
        info("-- Detection starts from : " + serverAddress);
        Map<String, Object> res = getNatType(serverAddress);
        info("-- Detection Result: " + res.get("NAT"));
        info("-- External Address: " + res.get("MAPPED-ADDRESS"));
        info("----------------------------------------------------------------");
    }

    static String HOST;
    static int PORT;

    static {
        try {
            HOST = Hub.getLocalAddressString();
            Random random = new Random();
            PORT = 19900 + random.nextInt(100);
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    static InetSocketAddress[] servers = {
            new InetSocketAddress(StunServer.HOST, StunServer.PORT),

            //new InetSocketAddress("stun.xten.com", 3478),
            //new InetSocketAddress("stun.voipbuster.com", 3478),
            //new InetSocketAddress("stun.sipgate.net", 3478),
            //new InetSocketAddress("stun.ekiga.net", 3478),
            //new InetSocketAddress("stun.schlund.de", 3478),
            new InetSocketAddress("stun.voipstunt.com", 3478),
            //new InetSocketAddress("stun.counterpath.com", 3478),
            //new InetSocketAddress("stun.1und1.de", 3478),
            //new InetSocketAddress("stun.gmx.net", 3478),
            //new InetSocketAddress("stun.callwithus.com", 3478),
            //new InetSocketAddress("stun.counterpath.net", 3478),
            //new InetSocketAddress("stun.internetcalls.com", 3478),
    };

    public static void main(String[] args) throws IOException {

        InetSocketAddress local = new InetSocketAddress(HOST, PORT);
        StunClient client = new StunClient(local);

        client.start();

        for (InetSocketAddress stun : servers) {
            client.detect(stun);
        }

        client.stop();
    }
}
