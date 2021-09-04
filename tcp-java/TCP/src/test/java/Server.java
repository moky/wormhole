
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.WeakHashMap;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.net.PlainHub;
import chat.dim.port.Arrival;
import chat.dim.port.Departure;
import chat.dim.port.Gate;
import chat.dim.startrek.PlainArrival;
import chat.dim.tcp.StreamChannel;

class ServerHub extends PlainHub implements Runnable {

    private final Map<SocketAddress, SocketChannel> slaves = new WeakHashMap<>();
    private SocketAddress localAddress = null;
    private ServerSocketChannel master = null;
    private boolean running = false;

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    void bind(SocketAddress local) throws IOException {
        ServerSocketChannel sock = master;
        if (sock != null && sock.isOpen()) {
            sock.close();
        }
        sock = ServerSocketChannel.open();
        sock.socket().bind(local);
        sock.configureBlocking(false);
        master = sock;
        localAddress = local;
    }

    boolean isRunning() {
        return running;
    }

    void start() {
        running = true;
        new Thread(this).start();
    }

    @Override
    public void run() {
        SocketChannel channel;
        SocketAddress remote;
        while (running) {
            try {
                channel = master.accept();
                if (channel != null) {
                    remote = channel.getRemoteAddress();
                    slaves.put(remote, channel);
                    connect(remote, localAddress);
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        SocketChannel sock = slaves.get(remote);
        if (sock == null) {
            throw new SocketException("failed to get channel: " + remote + " -> " + local);
        } else {
            return new StreamChannel(sock);
        }
    }
}

public class Server implements Runnable, Gate.Delegate {

    private final SocketAddress localAddress;

    private final TCPGate<ServerHub> gate;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        gate = new TCPGate<>(this);
        gate.hub = new ServerHub(gate);
    }

    @Override
    public void onStatusChanged(Gate.Status oldStatus, Gate.Status newStatus, SocketAddress remote, Gate gate) {
        TCPGate.info("!!! connection (" + remote + ") state changed: " + oldStatus + " -> " + newStatus);
    }

    @Override
    public void onReceived(Arrival ship, SocketAddress remote, Gate gate) {
        assert ship instanceof PlainArrival : "income ship error: " + ship;
        byte[] pack = ((PlainArrival) ship).getData();
        String text = new String(pack, StandardCharsets.UTF_8);
        TCPGate.info("<<< received (" + pack.length + " bytes) from " + remote + ": " + text);
        text = (counter++) + "# " + pack.length + " byte(s) received";
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
        TCPGate.info(">>> responding: " + text);
        send(data, remote);
    }
    static int counter = 0;

    @Override
    public void onSent(Departure ship, SocketAddress remote, Gate gate) {

    }

    @Override
    public void onError(Error error, Departure ship, SocketAddress remote, Gate gate) {

    }

    private void send(byte[] data, SocketAddress destination) {
        boolean ok = gate.send(data, destination);
        assert ok;
    }

    public void start() {
        try {
            gate.hub.bind(localAddress);
            gate.hub.start();
        } catch (IOException e) {
            e.printStackTrace();
        }
        new Thread(this).start();
    }

    @Override
    public void run() {
        while (gate.hub.isRunning()) {
            gate.hub.tick();
            if (gate.hub.getActivatedCount() == 0) {
                TCPGate.idle(8);
            }
        }
    }

    static String HOST;
    static final int PORT = 9394;

    static {
        try {
            HOST = Hub.getLocalAddressString();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {

        TCPGate.info("Starting server (" + HOST + ":" + PORT + ") ...");

        Server server = new Server(new InetSocketAddress(HOST, PORT));

        server.start();
    }
}
