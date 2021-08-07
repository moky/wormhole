
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.PackageConnection;
import chat.dim.type.Data;
import chat.dim.udp.DiscreteChannel;
import chat.dim.udp.PackageHub;

class ServerConnection extends PackageConnection {

    public ServerConnection(Channel byteChannel, SocketAddress remote, SocketAddress local) {
        super(byteChannel, remote, local);
    }

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        SocketAddress remote = super.receive(dst);
        if (remote != null) {
            Server.remoteAddress = remote;
        }
        return remote;
    }
}

class ServerHub extends PackageHub {

    private Connection primaryConnection = null;
    private Connection secondaryConnection = null;

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    private Connection createServerConnection(SocketAddress remote, SocketAddress local) {
        // create connection with channel
        ServerConnection conn = new ServerConnection(createChannel(remote, local), remote, local);
        // set delegate
        if (conn.getDelegate() == null) {
            conn.setDelegate(getDelegate());
        }
        // start FSM
        conn.start();
        return conn;
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) {
        if (local instanceof InetSocketAddress) {
            int port = ((InetSocketAddress) local).getPort();
            if (port == Server.SERVER_PORT) {
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

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) {
        if (local instanceof InetSocketAddress) {
            int port = ((InetSocketAddress) local).getPort();
            if (port == Server.SERVER_PORT) {
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

    static final String SERVER_Test = "192.168.0.111"; // Test
    static final String SERVER_GZ1 = "134.175.87.98"; // GZ-1
    static final String SERVER_HK2 = "129.226.128.17"; // HK-2

    static final InetSocketAddress CHANGED_ADDRESS = new InetSocketAddress(SERVER_HK2, 3478);
    static final InetSocketAddress NEIGHBOUR_SERVER = new InetSocketAddress(SERVER_HK2, 3478);

    static final String SERVER_IP = SERVER_Test;
    static final int SERVER_PORT = 3478;
    static final int CHANGE_PORT = 3479;

    private boolean running = false;

    public final PackageHub hub;

    public Server(String host, int port, int changePort) {
        super(host, port, changePort);
        hub = new ServerHub(this);
    }

    @Override
    protected void info(String msg) {
        Date currentTime = new Date();
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String dateString = formatter.format(currentTime);
        System.out.printf("[%s] %s\n", dateString, msg);
    }

    @Override
    public void onConnectionStateChanging(Connection connection, ConnectionState current, ConnectionState next) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + current + " -> " + next);
    }

    @Override
    public void onConnectionReceivedData(Connection connection, SocketAddress remote, byte[] data) {
        if (data != null && data.length > 0) {
            chunks.add(data);
        }
    }

    private final List<byte[]> chunks = new ArrayList<>();

    @Override
    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        try {
            hub.sendMessage(data, source, destination);
            return 0;
        } catch (IOException e) {
            e.printStackTrace();
            return -1;
        }
    }

    /**
     *  Received data from any socket
     *
     * @return data and remote address
     */
    public byte[] receive() {
        byte[] data = null;
        long timeout = (new Date()).getTime() + 2000;
        while (running) {
            if (chunks.size() == 0) {
                // drive hub to receive data
                hub.tick();
            }
            if (chunks.size() > 0) {
                data = chunks.remove(0);
                break;
            }
            if (timeout < (new Date()).getTime()) {
                break;
            }
            Client.idle(128);
        }
        return data;
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

        byte[] data;
        running = true;
        while (running) {
            try {
                data = receive();
                if (data == null) {
                    Client.idle(128);
                    continue;
                }
                handle(new Data(data), (InetSocketAddress) remoteAddress);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    static SocketAddress primaryAddress;
    static SocketAddress secondaryAddress;
    static SocketAddress remoteAddress;

    static DiscreteChannel primaryChannel;
    static DiscreteChannel secondaryChannel;

    public static void main(String[] args) throws IOException {

        primaryAddress = new InetSocketAddress(SERVER_IP, SERVER_PORT);
        secondaryAddress = new InetSocketAddress(SERVER_IP, CHANGE_PORT);
        remoteAddress = null;

        primaryChannel = new DiscreteChannel(DatagramChannel.open());
        primaryChannel.bind(primaryAddress);
        primaryChannel.configureBlocking(false);

        secondaryChannel = new DiscreteChannel(DatagramChannel.open());
        secondaryChannel.bind(secondaryAddress);
        secondaryChannel.configureBlocking(false);

        Server server = new Server(SERVER_IP, SERVER_PORT, CHANGE_PORT);
        server.changedAddress = CHANGED_ADDRESS;
        server.neighbour = NEIGHBOUR_SERVER;
        new Thread(server).start();
    }
}
