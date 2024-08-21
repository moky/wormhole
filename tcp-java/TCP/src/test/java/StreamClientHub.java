
import java.net.SocketAddress;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.tcp.ClientHub;

class StreamClientHub extends ClientHub {

    public StreamClientHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Channel getChannel(SocketAddress remote, SocketAddress local) {
        return super.getChannel(remote, null);
    }

    @Override
    protected void setChannel(SocketAddress remote, SocketAddress local, Channel channel) {
        super.setChannel(remote, null, channel);
    }

    @Override
    protected void removeChannel(SocketAddress remote, SocketAddress local, Channel channel) {
        super.removeChannel(remote, null, channel);
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
