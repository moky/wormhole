
import java.net.SocketAddress;

import chat.dim.net.Connection;
import chat.dim.tcp.ServerHub;

class StreamServerHub extends ServerHub {

    public StreamServerHub(Connection.Delegate delegate, boolean isDaemon) {
        super(delegate, isDaemon);
    }

    @Override
    protected Connection getConnection(SocketAddress remote, SocketAddress local) {
        return super.getConnection(remote, null);
    }

    @Override
    protected void setConnection(SocketAddress remote, SocketAddress local, Connection conn) {
        super.setConnection(remote, null, conn);
    }

    @Override
    protected void removeConnection(SocketAddress remote, SocketAddress local, Connection conn) {
        super.removeConnection(remote, null, conn);
    }
}
