
import java.net.SocketAddress;
import java.nio.charset.StandardCharsets;

import chat.dim.net.Connection;
import chat.dim.net.Hub;
import chat.dim.port.Docker;
import chat.dim.startrek.PlainDocker;
import chat.dim.startrek.StarGate;

public class TCPGate<H extends Hub> extends StarGate {

    H hub = null;

    public TCPGate(Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Connection getConnection(SocketAddress remote) {
        return hub.getConnection(remote, null);
    }

    @Override
    protected Docker createDocker(SocketAddress remote, byte[] data) {
        return new PlainDocker(remote, data, this);
    }

    static void info(String msg) {
        System.out.printf("%s\n", msg);
    }
    static void info(byte[] data) {
        info(new String(data, StandardCharsets.UTF_8));
    }

    static void idle(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
