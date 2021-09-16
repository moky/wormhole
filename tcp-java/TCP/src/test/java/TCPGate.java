
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.port.Docker;
import chat.dim.skywalker.Runner;
import chat.dim.startrek.PlainDocker;
import chat.dim.startrek.StarGate;

public class TCPGate<H extends Hub> extends StarGate implements Runnable {

    private boolean running = false;
    private H hub = null;

    public TCPGate(Delegate delegate) {
        super(delegate);
    }

    public H getHub() {
        return hub;
    }
    public void setHub(H h) {
        hub = h;
    }

    public void start() {
        new Thread(this).start();
    }

    public void stop() {
        running = false;
    }

    public boolean isRunning() {
        return running;
    }

    @Override
    public void run() {
        running = true;
        while (isRunning()) {
            if (!process()) {
                idle();
            }
        }
    }

    protected void idle() {
        Runner.idle(128);
    }

    @Override
    public boolean process() {
        boolean incoming = getHub().process();
        boolean outgoing = super.process();
        return incoming || outgoing;
    }

    @Override
    public Connection getConnection(SocketAddress remote, SocketAddress local) {
        return getHub().getConnection(remote, local);
    }

    @Override
    protected Docker createDocker(SocketAddress remote, SocketAddress local, List<byte[]> data) {
        // TODO: check data format before creating docker
        return new PlainDocker(remote, local, this);
    }

    @Override
    protected List<byte[]> cacheAdvanceParty(byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {
        // TODO: cache the advance party before decide which docker to use
        List<byte[]> array = new ArrayList<>();
        if (data != null) {
            array.add(data);
        }
        return array;
    }

    @Override
    protected void clearAdvanceParty(SocketAddress source, SocketAddress destination, Connection connection) {
        // TODO: remove advance party for this connection
    }

    @Override
    public void onStateChanged(ConnectionState previous, ConnectionState current, Connection connection) {
        super.onStateChanged(previous, current, connection);
        info("connection state changed: " + previous + " -> " + current + ", " + connection);
    }

    public void send(byte[] payload, SocketAddress source, SocketAddress destination) {
        Docker worker = getDocker(destination, source, null);
        ((PlainDocker) worker).send(payload);
    }

    static void info(byte[] data) {
        info(new String(data, StandardCharsets.UTF_8));
    }
    static void info(String msg) {
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String now = formatter.format(new Date());
        System.out.printf("[%s] %s\n", now, msg);
    }
    static void error(String msg) {
        System.out.printf("ERROR> %s\n", msg);
    }
}
