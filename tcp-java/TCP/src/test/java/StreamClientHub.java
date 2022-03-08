
import java.net.SocketAddress;

import chat.dim.net.Connection;
import chat.dim.tcp.ClientHub;

class StreamClientHub extends ClientHub {

    public StreamClientHub(Connection.Delegate delegate) {
        super(delegate);
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
