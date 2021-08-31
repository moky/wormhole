import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.net.RawDataHub;
import chat.dim.udp.PackageChannel;

import java.io.IOException;
import java.net.SocketAddress;
import java.net.SocketException;
import java.nio.channels.DatagramChannel;
import java.util.Map;
import java.util.WeakHashMap;

public class StunHub extends RawDataHub {

    private final Map<SocketAddress, Connection<byte[]>> connections = new WeakHashMap<>();
    private final Map<SocketAddress, DatagramChannel> channels = new WeakHashMap<>();
    private boolean running = false;

    public StunHub(Connection.Delegate<byte[]> delegate) {
        super(delegate);
    }

    void bind(SocketAddress local) throws IOException {
        DatagramChannel sock = channels.get(local);
        if (sock == null) {
            sock = DatagramChannel.open();
            sock.socket().bind(local);
            sock.configureBlocking(false);
            channels.put(local, sock);
        }
        connect(null, local);
    }

    boolean isRunning() {
        return running;
    }

    void start() {
        running = true;
    }

    void stop() {
        running = false;
    }

    @Override
    protected Connection<byte[]> createConnection(SocketAddress remote, SocketAddress local) throws IOException {
        Connection<byte[]> conn = connections.get(local);
        if (conn == null) {
            conn = super.createConnection(remote, local);
            connections.put(local, conn);
        }
        return conn;
    }

    @Override
    protected Channel createChannel(SocketAddress remote, SocketAddress local) throws IOException {
        DatagramChannel sock = channels.get(local);
        if (sock == null) {
            throw new SocketException("failed to get channel: " + remote + " -> " + local);
        } else {
            return new PackageChannel(sock);
        }
    }
}
