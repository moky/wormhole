
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.net.SocketException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.stun.Client;

public class StunClient extends Client implements Runnable, Connection.Delegate<byte[]> {

    private final SocketAddress remoteAddress;
    private final StunHub hub;

    StunClient(InetSocketAddress local, SocketAddress remote) {
        super(local);
        remoteAddress = remote;
        hub = new StunHub(this);
    }

    public void start() {
        try {
            hub.bind(sourceAddress);
            hub.start();
        } catch (IOException e) {
            e.printStackTrace();
        }
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
    public void onConnectionStateChanged(Connection connection, ConnectionState previous, ConnectionState current) {
        info("!!! connection ("
                + connection.getLocalAddress() + ", "
                + connection.getRemoteAddress() + ") state changed: "
                + previous + " -> " + current);
    }

    @Override
    public void onConnectionDataReceived(Connection<byte[]> connection, SocketAddress remote, byte[] pack) {
        if (pack != null && pack.length > 0) {
            chunks.add(pack);
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
            idle(256);
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

        System.out.printf("connecting to STUN server: (%s:%d) ...\n", StunServer.HOST, StunServer.PORT);

        InetSocketAddress local = new InetSocketAddress(HOST, PORT);
        InetSocketAddress remote = new InetSocketAddress(StunServer.HOST, StunServer.PORT);
        StunClient client = new StunClient(local, remote);

        client.start();
        client.detect(remote);
        client.stop();
    }
}
