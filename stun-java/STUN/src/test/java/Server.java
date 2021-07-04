
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.text.SimpleDateFormat;
import java.util.Date;

import chat.dim.mtp.DataType;
import chat.dim.mtp.Package;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.PackageConnection;
import chat.dim.type.Data;
import chat.dim.udp.ActivePackageHub;
import chat.dim.udp.DiscreteChannel;

class ServerConnection extends PackageConnection {

    public ServerConnection(Channel byteChannel, SocketAddress remote, SocketAddress local) {
        super(byteChannel, remote, local);
    }

    @Override
    protected Channel connect(SocketAddress remote, SocketAddress local) {
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

    @Override
    public SocketAddress receive(ByteBuffer dst) throws IOException {
        SocketAddress remote = super.receive(dst);
        if (remote != null) {
            Server.remoteAddress = remote;
        }
        return remote;
    }
}

class ServerHub extends ActivePackageHub {

    public ServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) {
        Channel channel;
        if (local instanceof InetSocketAddress) {
            int port = ((InetSocketAddress) local).getPort();
            if (port == Server.SERVER_PORT) {
                channel = Server.primaryChannel;
            } else if (port == Server.CHANGE_PORT) {
                channel = Server.secondaryChannel;
            } else {
                throw new IllegalArgumentException("port not defined: " + port);
            }
        } else {
            throw new NullPointerException("local address error: " + local);
        }
        ServerConnection conn = new ServerConnection(channel, remote, local);
        // set delegate
        Connection.Delegate delegate = getDelegate();
        if (delegate != null) {
            conn.setDelegate(delegate);
        }
        // start FSM
        conn.start();
        return conn;
    }
}

public class Server extends chat.dim.stun.Server implements Runnable, Connection.Delegate {

    static final String SERVER_Test = "192.168.31.91"; // Test
    static final String SERVER_GZ1 = "134.175.87.98"; // GZ-1
    static final String SERVER_HK2 = "129.226.128.17"; // HK-2

    static final InetSocketAddress CHANGED_ADDRESS = new InetSocketAddress(SERVER_HK2, 3478);
    static final InetSocketAddress NEIGHBOUR_SERVER = new InetSocketAddress(SERVER_HK2, 3478);

    static final String SERVER_IP = SERVER_Test;
    static final int SERVER_PORT = 3478;
    static final int CHANGE_PORT = 3479;

    private boolean running = false;

    public final ActivePackageHub hub;

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
        if (next.equals(ConnectionState.EXPIRED)) {
            assert connection instanceof PackageConnection : "connection error: " + connection;
            ((PackageConnection) connection).heartbeat(connection.getRemoteAddress());
        }
    }

    @Override
    public int send(byte[] data, SocketAddress source, SocketAddress destination) {
        Package pack = Package.create(DataType.Message, new Data(data));
        return hub.sendPackage(pack, source, destination) ? 0 : -1;
    }

    private byte[] receive(SocketAddress source, SocketAddress destination) {
        Package pack = hub.receivePackage(source, destination);
        return pack == null ? null : pack.body.getBytes();
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
            data = receive(null, primaryAddress);
            if (data != null) {
                break;
            }
            data = receive(null, secondaryAddress);
            if (data != null) {
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
