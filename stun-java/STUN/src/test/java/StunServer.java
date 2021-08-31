
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.text.SimpleDateFormat;
import java.util.Date;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.stun.Server;
import chat.dim.type.Data;

public class StunServer extends Server implements Runnable, Connection.Delegate<byte[]> {

    private final StunHub hub;

    public StunServer(InetSocketAddress sourceAddress, int changePort,
                  InetSocketAddress changedAddress, InetSocketAddress neighbour) {
        super(sourceAddress, changePort, changedAddress, neighbour);
        hub = new StunHub(this);
    }

    public void start() {
        try {
            SocketAddress secondaryAddress = new InetSocketAddress(sourceAddress.getAddress(), changePort);
            hub.bind(sourceAddress);
            hub.bind(secondaryAddress);
            hub.start();
        } catch (IOException e) {
            e.printStackTrace();
        }

        info("STUN server started");
        info("source address: " + sourceAddress + ", another port: " + changePort + ", neighbour server: " + neighbour);
        info("changed address: " + changedAddress);

        new Thread(this).start();
    }

    void stop() {
        hub.stop();
    }

    @Override
    public void run() {
        while (hub.isRunning()) {
            hub.tick();
            if (hub.getActivatedCount() == 0) {
                idle(8);
            }
        }
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

    @Override
    public void onConnectionStateChanged(Connection connection, ConnectionState previous, ConnectionState current) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + previous + " -> " + current);
    }

    @Override
    public void onConnectionDataReceived(Connection<byte[]> connection, SocketAddress remote, byte[] pack) {
        if (pack != null && pack.length > 0) {
            handle(new Data(pack), (InetSocketAddress) remote);
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

    public static void main(String[] args) {

        InetSocketAddress primary = new InetSocketAddress(HOST, PORT);

        StunServer server = new StunServer(primary, CHANGE_PORT, CHANGED_ADDRESS, NEIGHBOUR_SERVER);

        server.start();
    }
}
