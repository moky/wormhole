
import java.io.IOException;
import java.lang.ref.WeakReference;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

import chat.dim.net.BaseConnection;
import chat.dim.net.BaseHub;
import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.udp.PackageChannel;

class ClientHub extends BaseHub {

    private final WeakReference<Connection.Delegate> delegateRef;

    private Channel localChannel = null;

    public ClientHub(Connection.Delegate delegate) {
        super();
        delegateRef = new WeakReference<>(delegate);
    }

    public Connection.Delegate getDelegate() {
        return delegateRef.get();
    }

    @Override
    protected Connection createConnection(SocketAddress remote, SocketAddress local) throws IOException {
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

    private Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        if (localChannel == null) {
            localChannel = new PackageChannel(null, local);
            localChannel.configureBlocking(false);
        }
        return localChannel;
    }
}

public class Client extends chat.dim.stun.Client implements Connection.Delegate {

    public Client(String host, int port) {
        super(host, port);
    }

    @Override
    public void onConnectionStateChanged(Connection connection, ConnectionState previous, ConnectionState current) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + previous + " -> " + current);
    }

    @Override
    public void onConnectionDataReceived(Connection connection, SocketAddress remote, Object wrapper, byte[] payload) {
        if (payload != null && payload.length > 0) {
            chunks.add(payload);
        }
    }

    private final List<byte[]> chunks = new ArrayList<>();

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

    @Override
    public byte[] receive() {
        byte[] data = null;
        long timeout = (new Date()).getTime() + 2000;
        while (true) {
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
            Client.idle(256);
        }
        info("received " + (data == null ? 0 : data.length) + " bytes from " + remoteAddress);
        return data;
    }

    @Override
    protected void info(String msg) {
        Date currentTime = new Date();
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String dateString = formatter.format(currentTime);
        System.out.printf("[%s] %s\n", dateString, msg);
    }

    static void idle(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
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
    static final int PORT = 9527;

    static {
        try {
            HOST = Hub.getLocalAddressString();
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    static SocketAddress remoteAddress;

    static ClientHub hub;

    public static void main(String[] args) {

        //remoteAddress = new InetSocketAddress("stun.xten.com", 3478);
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

        remoteAddress = new InetSocketAddress(Server.HOST, Server.PORT);
        System.out.printf("connecting to STUN server: %s ...\n", remoteAddress);

        Client client = new Client(HOST, PORT);

        hub = new ClientHub(client);

        client.detect(remoteAddress);

        System.exit(0);
    }
}
