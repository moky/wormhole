
import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.channels.DatagramChannel;
import java.text.SimpleDateFormat;
import java.util.Date;

import chat.dim.net.BaseConnection;
import chat.dim.net.BaseHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.type.Data;
import chat.dim.udp.DiscreteChannel;

class ServerHub extends BaseHub {

    private final WeakReference<Connection.Delegate> delegateRef;

    private Connection primaryConnection = null;
    private Connection secondaryConnection = null;

    public ServerHub(Connection.Delegate delegate) {
        super();
        delegateRef = new WeakReference<>(delegate);
    }

    public Connection.Delegate getDelegate() {
        return delegateRef.get();
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) {
        if (local instanceof InetSocketAddress) {
            int port = ((InetSocketAddress) local).getPort();
            if (port == Server.PORT) {
                if (primaryConnection == null) {
                    primaryConnection = createServerConnection(remote, local);
                }
                return primaryConnection;
            } else if (port == Server.CHANGE_PORT) {
                if (secondaryConnection == null) {
                    secondaryConnection = createServerConnection(remote, local);
                }
                return secondaryConnection;
            } else {
                throw new IllegalArgumentException("port not defined: " + port);
            }
        } else {
            throw new NullPointerException("local address error: " + local);
        }
    }

    private Connection createServerConnection(SocketAddress remote, SocketAddress local) {
        // create connection with channel
        BaseConnection conn = new BaseConnection(createChannel(remote, local), remote, local);
        // set delegate
        if (conn.getDelegate() == null) {
            conn.setDelegate(getDelegate());
        }
        // start FSM
        conn.start();
        return conn;
    }

    private Channel createChannel(SocketAddress remote, SocketAddress local) {
        if (local instanceof InetSocketAddress) {
            int port = ((InetSocketAddress) local).getPort();
            if (port == Server.PORT) {
                return Server.primaryChannel;
            } else if (port == Server.CHANGE_PORT) {
                return Server.secondaryChannel;
            } else {
                throw new IllegalArgumentException("port not defined: " + port);
            }
        } else {
            throw new NullPointerException("local address error: " + local);
        }
    }
}

public class Server extends chat.dim.stun.Server implements Runnable, Connection.Delegate {

    private boolean running;

    public Server(String host, int port, int changePort,
                  InetSocketAddress changedAddress, InetSocketAddress neighbour) {
        super(host, port, changePort, changedAddress, neighbour);
        running = false;
    }

    @Override
    protected void info(String msg) {
        Date currentTime = new Date();
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String dateString = formatter.format(currentTime);
        System.out.printf("[%s] %s\n", dateString, msg);
    }

    @Override
    public void run() {
        try {
            hub.connect(null, primaryAddress);
            hub.connect(null, secondaryAddress);
        } catch (IOException e) {
            e.printStackTrace();
        }

        info("STUN server started");
        info("source address: " + sourceAddress + ", another port: " + changePort + ", neighbour server: " + neighbour);
        info("changed address: " + changedAddress);

        running = true;
        while (running) {
            hub.tick();
            Client.idle(128);
        }
    }

    @Override
    public void onConnectionStateChanging(Connection connection, ConnectionState current, ConnectionState next) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + current + " -> " + next);
    }

    @Override
    public void onConnectionDataReceived(Connection connection, SocketAddress remote, Object wrapper, byte[] payload) {
        if (payload != null && payload.length > 0) {
            handle(new Data(payload), (InetSocketAddress) remote);
        }
    }

    @Override
    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        try {
            hub.send(data, source, destination);
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

    static SocketAddress primaryAddress;
    static SocketAddress secondaryAddress;

    static DiscreteChannel primaryChannel;
    static DiscreteChannel secondaryChannel;

    static ServerHub hub;

    public static void main(String[] args) throws IOException {

        primaryAddress = new InetSocketAddress(HOST, PORT);
        secondaryAddress = new InetSocketAddress(HOST, CHANGE_PORT);

        primaryChannel = new DiscreteChannel(DatagramChannel.open());
        primaryChannel.bind(primaryAddress);
        primaryChannel.configureBlocking(false);

        secondaryChannel = new DiscreteChannel(DatagramChannel.open());
        secondaryChannel.bind(secondaryAddress);
        secondaryChannel.configureBlocking(false);

        Server server = new Server(HOST, PORT, CHANGE_PORT, CHANGED_ADDRESS, NEIGHBOUR_SERVER);

        hub = new ServerHub(server);

        new Thread(server).start();
    }
}
