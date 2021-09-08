
import java.net.SocketAddress;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Docker;
import chat.dim.skywalker.Runner;
import chat.dim.startrek.PlainDocker;
import chat.dim.startrek.StarGate;

public class UDPGate<H extends Hub> extends StarGate implements Runnable {

    private boolean running = false;
    H hub = null;

    public UDPGate(Delegate delegate) {
        super(delegate);
    }

    public void start() {
        new Thread(this).start();
    }

    public void stop() {
        running = false;
    }

    @Override
    public void run() {
        running = true;
        while (running) {
            if (!process()) {
                Runner.idle(8);
            }
        }
    }

    @Override
    public boolean process() {
        boolean activated = hub.process();
        boolean busy = super.process();
        return activated || busy;
    }

    @Override
    protected Connection getConnection(SocketAddress remote, SocketAddress local) {
        return hub.getConnection(remote, local);
    }

    @Override
    protected Docker createDocker(SocketAddress remote, SocketAddress local, List<byte[]> data) {
        // TODO: check data format before creating docker
        return new PlainDocker(remote, local, data, this);
    }

    @Override
    protected List<byte[]> cacheAdvanceParty(byte[] data, SocketAddress source, SocketAddress destination, Connection connection) {
        // TODO: cache the advance party before decide which docker to use
        return null;
    }

    @Override
    protected void clearAdvanceParty(SocketAddress source, SocketAddress destination, Connection connection) {
        // TODO: remove advance party for this connection
    }

    void sendData(byte[] payload, SocketAddress source, SocketAddress destination) {
        Docker worker = getDocker(destination, source, null);
        ((PlainDocker) worker).sendData(payload);
    }

    static void info(String msg) {
        Date currentTime = new Date();
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String dateString = formatter.format(currentTime);
        System.out.printf("[%s] %s\n", dateString, msg);
    }
    static void error(String msg) {
        System.out.printf("ERROR> %s\n", msg);
    }
}
