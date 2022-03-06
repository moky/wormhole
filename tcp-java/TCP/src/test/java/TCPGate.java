
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import chat.dim.net.ActiveConnection;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.port.Docker;
import chat.dim.skywalker.Runner;
import chat.dim.startrek.PlainDocker;
import chat.dim.startrek.StarGate;
import chat.dim.threading.Daemon;

public class TCPGate<H extends Hub> extends StarGate implements Runnable {

    private H hub = null;

    private final Daemon daemon;
    private boolean running;

    public TCPGate(Delegate delegate, boolean isDaemon) {
        super(delegate);
        daemon = new Daemon(this, isDaemon);
        running = false;
    }
    public TCPGate(Delegate delegate) {
        this(delegate, true);
    }

    public H getHub() {
        return hub;
    }
    public void setHub(H h) {
        hub = h;
    }

    public boolean isRunning() {
        return running;
    }

    public void start() {
        stop();
        running = true;
        daemon.start();
    }

    public void stop() {
        running = false;
        daemon.stop();
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
        try {
            boolean incoming = getHub().process();
            boolean outgoing = super.process();
            return incoming || outgoing;
        } catch (Throwable e) {
            e.printStackTrace();
            return false;
        }
    }

    @Override
    public Connection getConnection(SocketAddress remote, SocketAddress local) {
        return getHub().connect(remote, null);
    }

    @Override
    protected Docker createDocker(SocketAddress remote, SocketAddress local, List<byte[]> data) {
        // TODO: check data format before creating docker
        return new PlainDocker(remote, null, this);
    }

    @Override
    protected Docker getDocker(SocketAddress remote, SocketAddress local) {
        return super.getDocker(remote, null);
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
    protected void heartbeat(Connection connection) {
        // let the client to do the job
        if (connection instanceof ActiveConnection) {
            super.heartbeat(connection);
        }
    }

    @Override
    public void onStateChanged(ConnectionState previous, ConnectionState current, Connection connection) {
        super.onStateChanged(previous, current, connection);
        info("connection state changed: " + previous + " -> " + current + ", " + connection);
    }

    @Override
    public void onError(Throwable error, byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {
        error("connection error: " + error + ", " + connection);
    }

    public Docker getDocker(SocketAddress remote, SocketAddress local, List<byte[]> data) {
        Docker docker = getDocker(remote, local);
        if (docker == null) {
            docker = createDocker(remote, local, data);
            assert docker != null : "failed to create docker: " + remote + ", " + local;
            putDocker(docker);
        }
        return docker;
    }

    public boolean send(byte[] payload, SocketAddress source, SocketAddress destination) {
        Docker worker = getDocker(destination, source, null);
        if (worker instanceof PlainDocker) {
            return ((PlainDocker) worker).send(payload);
        } else {
            return false;
        }
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
