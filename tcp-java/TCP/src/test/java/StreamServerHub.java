
import java.net.SocketAddress;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.tcp.ServerHub;

class StreamServerHub extends ServerHub {

    public StreamServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Channel getChannel(SocketAddress remote, SocketAddress local) {
        return super.getChannel(remote, null);
    }

    @Override
    protected Channel setChannel(SocketAddress remote, SocketAddress local, Channel channel) {
        return super.setChannel(remote, null, channel);
    }

    @Override
    protected Channel removeChannel(SocketAddress remote, SocketAddress local, Channel channel) {
        return super.removeChannel(remote, null, channel);
    }

    @Override
    protected Connection getConnection(SocketAddress remote, SocketAddress local) {
        return super.getConnection(remote, null);
    }

    @Override
    protected Connection setConnection(SocketAddress remote, SocketAddress local, Connection conn) {
        return super.setConnection(remote, null, conn);
    }

    @Override
    protected Connection removeConnection(SocketAddress remote, SocketAddress local, Connection conn) {
        return super.removeConnection(remote, null, conn);
    }

}
