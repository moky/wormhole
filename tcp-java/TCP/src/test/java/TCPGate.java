
import java.io.IOException;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;

import chat.dim.net.BaseHub;
import chat.dim.net.Connection;
import chat.dim.port.Docker;
import chat.dim.startrek.PlainDocker;
import chat.dim.startrek.StarGate;

public class TCPGate<H extends BaseHub> extends StarGate {

    H hub = null;

    public TCPGate(Delegate delegate) {
        super(delegate);
    }

    public void start() {
        setup();
        new Thread(this).start();
    }

    @Override
    public boolean process() {
        hub.tick();
        boolean available = hub.getActivatedCount() > 0;
        boolean busy = super.process();
        return available || busy;
    }

    @Override
    protected Connection getConnection(SocketAddress remote) {
        return hub.getConnection(remote, null);
    }

    @Override
    protected Connection connect(SocketAddress remote) throws IOException {
        return hub.connect(remote, null);
    }

    @Override
    protected Docker createDocker(SocketAddress remote, byte[] data) {
        // TODO: check data format before creating docker
        return new PlainDocker(remote, data, this);
    }

    @Override
    public Docker getDocker(SocketAddress remote) {
        Docker worker = super.getDocker(remote);
        if (worker == null) {
            if (getConnection(remote) != null) {
                worker = createDocker(remote, null);
                if (worker != null) {
                    setDocker(remote, worker);
                }
            }
        }
        return worker;
    }

    void sendMessage(byte[] payload, SocketAddress destination) {
        Docker worker = getDocker(destination);
        assert worker instanceof PlainDocker : "docker error: " + worker;
        ((PlainDocker) worker).sendData(payload);
    }

    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }
    static void info(byte[] data) {
        info(new String(data, StandardCharsets.UTF_8));
    }
    static void error(String msg) {
        System.out.printf("ERROR> %s\n", msg);
    }

    static void idle(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
