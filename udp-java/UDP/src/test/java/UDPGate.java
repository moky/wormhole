
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import chat.dim.mtp.DataType;
import chat.dim.mtp.Package;
import chat.dim.mtp.PackageDocker;
import chat.dim.net.BaseConnection;
import chat.dim.net.Connection;
import chat.dim.net.ConnectionState;
import chat.dim.net.Hub;
import chat.dim.port.Docker;
import chat.dim.port.Gate;
import chat.dim.skywalker.Runner;
import chat.dim.startrek.StarGate;
import chat.dim.type.Data;


class UDPDocker extends PackageDocker {

    UDPDocker(SocketAddress remote, SocketAddress local, StarGate gate) {
        super(remote, local, gate);
    }

    @Override
    protected Hub getHub() {
        Gate gate = getGate();
        if (gate instanceof UDPGate) {
            //noinspection rawtypes
            return ((UDPGate) gate).getHub();
        }
        return null;
    }
}

public class UDPGate<H extends Hub> extends StarGate implements Runnable {

    private boolean running = false;
    private H hub = null;

    public UDPGate(Delegate delegate) {
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
        return getHub().connect(remote, local);
    }

    @Override
    protected Docker createDocker(SocketAddress remote, SocketAddress local, List<byte[]> data) {
        // TODO: check data format before creating docker
        return new UDPDocker(remote, null, this);
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
        if (connection instanceof BaseConnection) {
            if (((BaseConnection) connection).isActivated) {
                super.heartbeat(connection);
            }
        }
    }

    private void kill(SocketAddress remote, SocketAddress local, Connection connection) {
        // if conn is null, disconnect with (remote, local);
        // else, disconnect with connection when local address matched.
        connection = getHub().disconnect(remote, local, connection);
        // if connection is not activated, means it's a server connection,
        // remove the docker too.
        if (connection instanceof BaseConnection) {
            if (!((BaseConnection) connection).isActivated) {
                // remove docker for server connection
                remote = connection.getRemoteAddress();
                local = connection.getLocalAddress();
                removeDocker(remote, local, null);
            }
        }
    }

    @Override
    public void onStateChanged(ConnectionState previous, ConnectionState current, Connection connection) {
        super.onStateChanged(previous, current, connection);
        info("connection state changed: " + previous + " -> " + current + ", " + connection);
        if (current != null && current.equals(ConnectionState.ERROR)) {
            error("remove error connection: " + connection);
            kill(null, null, connection);
        }
    }

    @Override
    public void onError(Throwable error, byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {
        if (connection == null) {
            // failed to receive data
            kill(source, destination, null);
        } else {
            // failed to send data
            kill(destination, source, connection);
        }
    }

    public void sendCommand(byte[] body, SocketAddress source, SocketAddress destination) {
        Package pack = Package.create(DataType.COMMAND, new Data(body));
        send(pack/*, Departure.Priority.SLOWER.value*/, source, destination);
    }

    public void sendMessage(byte[] body, SocketAddress source, SocketAddress destination) {
        Package pack = Package.create(DataType.MESSAGE, new Data(body));
        send(pack, source, destination);
    }

    public void send(Package pack, SocketAddress source, SocketAddress destination) {
        Docker worker = getDocker(destination, source);
        if (worker == null) {
            worker = createDocker(destination, source, null);
            assert worker != null : "failed to create docker: " + destination + ", " + source;
            putDocker(worker);
        }
        ((PackageDocker) worker).send(pack);
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
