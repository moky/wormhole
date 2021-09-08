
import java.io.IOException;
import java.net.SocketAddress;
import java.util.List;

import chat.dim.mtp.DataType;
import chat.dim.mtp.Package;
import chat.dim.mtp.PackageDocker;
import chat.dim.net.BaseHub;
import chat.dim.net.Connection;
import chat.dim.port.Docker;
import chat.dim.startrek.StarGate;
import chat.dim.type.Data;

public class UDPGate<H extends BaseHub> extends StarGate {

    H hub = null;

    public UDPGate(Delegate delegate) {
        super(delegate);
    }

    public void start() {
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

    public void disconnect(SocketAddress remote, SocketAddress local) throws IOException {
        hub.disconnect(remote, local);
    }

    @Override
    protected Docker createDocker(SocketAddress remote,
                                                                                   SocketAddress local,
                                                                                   List<byte[]> data) {
        // TODO: check data format before creating docker
        return new PackageDocker(remote, local, data, this);
    }

    void sendCommand(byte[] body, SocketAddress source, SocketAddress destination) {
        Package pack = Package.create(DataType.COMMAND, new Data(body));
        Object worker = getDocker(destination, source, true);
        ((PackageDocker) worker).sendPackage(pack);
    }

    void sendMessage(byte[] body, SocketAddress source, SocketAddress destination) {
        Package pack = Package.create(DataType.MESSAGE, new Data(body));
        Object worker = getDocker(destination, source, true);
        ((PackageDocker) worker).sendPackage(pack);
    }

    static void info(String msg) {
        System.out.printf("%s\n", msg);
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
