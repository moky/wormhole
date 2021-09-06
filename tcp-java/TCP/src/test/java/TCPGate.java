
import java.io.IOException;
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;

import chat.dim.net.BaseHub;
import chat.dim.net.Connection;
import chat.dim.port.Docker;
import chat.dim.startrek.PlainArrival;
import chat.dim.startrek.PlainDeparture;
import chat.dim.startrek.PlainDocker;
import chat.dim.startrek.StarGate;

public class TCPGate<H extends BaseHub> extends StarGate<PlainDeparture, PlainArrival, Object> {

    H hub = null;

    public TCPGate(Delegate<PlainDeparture, PlainArrival, Object> delegate) {
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
    protected Connection getConnection(SocketAddress remote, SocketAddress local) {
        return hub.getConnection(remote, local);
    }

    @Override
    protected Connection connect(SocketAddress remote, SocketAddress local) throws IOException {
        return hub.connect(remote, local);
    }

    @Override
    protected Docker<PlainDeparture, PlainArrival, Object> createDocker(SocketAddress remote, SocketAddress local,
                                                                        List<byte[]> data) {
        // TODO: check data format before creating docker
        return new PlainDocker(remote, local, data, this);
    }

    void sendMessage(byte[] payload, SocketAddress source, SocketAddress destination) {
        Object worker = getDocker(destination, source, true);
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
