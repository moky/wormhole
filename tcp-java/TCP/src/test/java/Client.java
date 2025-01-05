
import java.io.IOError;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.Random;

import chat.dim.net.Hub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Porter;
import chat.dim.skywalker.Runner;
import chat.dim.stargate.TCPGate;
import chat.dim.startrek.PlainArrival;
import chat.dim.tcp.ClientHub;
import chat.dim.utils.Log;

public class Client implements Porter.Delegate {

    private final SocketAddress localAddress;
    private final SocketAddress remoteAddress;

    private final TCPGate<ClientHub> gate;

    Client(SocketAddress local, SocketAddress remote) {
        super();
        localAddress = local;
        remoteAddress = remote;
        gate = new TCPGate<>(this, true);
        gate.setHub(new StreamClientHub(gate));
    }

    private TCPGate<ClientHub> getGate() {
        return gate;
    }

    public void start() {
        getGate().start();
    }

    void stop() {
        getGate().stop();
    }

    private void send(byte[] data) {
        boolean ok = getGate().sendMessage(data, remoteAddress, localAddress);
        assert ok;
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
        assert income instanceof PlainArrival : "arrival ship error: " + income;
        byte[] data = ((PlainArrival) income).getPayload();
        String text = new String(data, StandardCharsets.UTF_8);
        SocketAddress source = porter.getRemoteAddress();
        Log.info("<<< received (" + data.length + " bytes) from " + source + ": " + text);
    }

    @Override
    public void onPorterSent(Departure departure, Porter porter) {
        // plain departure has no response,
        // we would not know whether the task is success here
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

    public static void main(String[] args) {

        SocketAddress local = new InetSocketAddress(Client.HOST, Client.PORT);
        SocketAddress remote = new InetSocketAddress(Server.HOST, Server.PORT);
        Log.info("Connecting TCP server (" + local + "->" + remote + ") ...");

        Client client = new Client(local, remote);

        client.start();
        client.test();
        client.stop();

        Log.info("Terminated.");
    }

}
