
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
import chat.dim.startrek.PlainDeparture;
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

public class Server implements Gate.Delegate {

    private final SocketAddress localAddress;

    private final TCPGate<ServerHub> gate;

    public Server(SocketAddress local) {
        super();
        localAddress = local;
        gate = new TCPGate<>(this);
        gate.hub = new ServerHub(gate);
    }

    public void start() throws IOException {
        gate.hub.bind(localAddress);
        gate.hub.start();
        gate.start();
    }

    private void send(byte[] data, SocketAddress destination) {
        gate.sendMessage(data, destination);
    }

    //
    //  Gate Delegate
    //

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
        assert ship instanceof PlainDeparture;
        int bodyLen = ((PlainDeparture) ship).getPackage().length;
        TCPGate.info("message sent: " + bodyLen + " byte(s) to " + remote);
    }

    @Override
    public void onError(Error error, Departure ship, SocketAddress remote, Gate gate) {
        TCPGate.error(error.getMessage());
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

    static Server server;

    public static void main(String[] args) throws IOException {

        SocketAddress local = new InetSocketAddress(HOST, PORT);
        TCPGate.info("Starting TCP server (" + local + ") ...");

        server = new Server(local);

        server.start();
    }
}
