
import java.io.IOError;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.Random;

import chat.dim.mtp.Package;
import chat.dim.mtp.PackageArrival;
import chat.dim.mtp.PackageDeparture;
import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Porter;
import chat.dim.skywalker.Runner;
import chat.dim.stargate.UDPGate;
import chat.dim.udp.ClientHub;
import chat.dim.utils.Log;

public class Client implements Porter.Delegate {

    private final SocketAddress localAddress;
    private final SocketAddress remoteAddress;

    private final UDPGate<ClientHub> gate;

    Client(SocketAddress local, SocketAddress remote) {
        super();
        localAddress = local;
        remoteAddress = remote;
        gate = new UDPGate<>(this, true);
        gate.setHub(new PacketClientHub(gate));
    }

    private UDPGate<ClientHub> getGate() {
        return gate;
    }
    private ClientHub getHub() {
        return gate.getHub();
    }

    public void start() throws IOException {
        getHub().bind(localAddress);
        getHub().connect(remoteAddress, null);
        getGate().start();
    }

    void stop() {
        getGate().stop();
    }

    private void send(byte[] data) {
        boolean ok1 = getGate().sendMessage(data, remoteAddress, localAddress);
        boolean ok2 = getGate().sendCommand(data, remoteAddress, localAddress);
        assert ok1 && ok2;
    }

    //
    //  Gate Delegate
    //

    @Override
    public void onPorterStatusChanged(Porter.Status previous, Porter.Status current, Porter porter) {
        SocketAddress remote = porter.getRemoteAddress();
        SocketAddress local = porter.getLocalAddress();
        Log.info("!!! connection (" + remote + ", " + local + ") state changed: " + previous + " -> " + current);
    }

    @Override
    public void onPorterReceived(Arrival income, Porter porter) {
        assert income instanceof PackageArrival : "arrival ship error: " + income;
        Package pack = ((PackageArrival) income).getPackage();
        int headLen = pack.head.getSize();
        int bodyLen = pack.body.getSize();
        byte[] payload = pack.body.getBytes();
        String text = new String(payload, StandardCharsets.UTF_8);
        SocketAddress source = porter.getRemoteAddress();
        Log.info("<<< received (" + headLen + " + " + bodyLen + " bytes) from " + source + ": " + text);
    }

    @Override
    public void onPorterSent(Departure outgo, Porter porter) {
        assert outgo instanceof PackageDeparture : "departure ship error: " + outgo;
        Package pack = ((PackageDeparture) outgo).getPackage();
        int bodyLen = pack.head.bodyLength;
        if (bodyLen == -1) {
            bodyLen = pack.body.getSize();
        }
        SocketAddress destination = porter.getRemoteAddress();
        Log.info("message sent: " + bodyLen + " byte(s) to " + destination);
    }

    @Override
    public void onPorterFailed(IOError error, Departure departure, Porter porter) {
        Log.error(error.getMessage());
    }

    @Override
    public void onPorterError(IOError error, Departure departure, Porter porter) {
        Log.error(error.getMessage());
    }

    void test() {

        StringBuilder content = new StringBuilder();
        for (int index = 0; index < 1024; ++index) {
            content.append(" Hello!");
        }

        String text;
        byte[] data;
        Runner.sleep(5000);

        for (int index = 0; index < 16; ++index) {
            text = index + " sheep:" + content;
            data = text.getBytes();
            Log.info(">>> sending (" + data.length + " bytes): ");
            Log.info(text);
            send(data);
            Runner.sleep(2000);
        }

        Runner.sleep(60000);
    }

    static String HOST;
    static int PORT;

    static {
        try {
            HOST = Hub.getLocalAddressString();
            Random random = new Random();
            PORT = 9900 + random.nextInt(100);
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) throws IOException {

        SocketAddress local = new InetSocketAddress(Client.HOST, Client.PORT);
        SocketAddress remote = new InetSocketAddress(Server.HOST, Server.PORT);
        Log.info("Connecting UDP server (" + local + " -> " + remote + ") ...");

        Client client = new Client(local, remote);

        client.start();
        client.test();
        client.stop();

        Log.info("Terminated.");
    }

}
