
import java.net.SocketAddress;

import chat.dim.net.Channel;
import chat.dim.net.Connection;
import chat.dim.udp.ServerHub;

public class PacketServerHub extends ServerHub {

    public PacketServerHub(Connection.Delegate delegate) {
        super(delegate);
    }

    @Override
    protected Channel getChannel(SocketAddress remote, SocketAddress local) {
        Channel channel = super.getChannel(remote, local);
        if (channel == null && remote != null && local != null) {
            channel = super.getChannel(null, local);
        }
        return channel;
    }

    @Override
    protected Channel setChannel(SocketAddress remote, SocketAddress local, Channel channel) {
        return super.setChannel(remote, local, channel);
    }

    @Override
    protected Channel removeChannel(SocketAddress remote, SocketAddress local, Channel channel) {
        return super.removeChannel(remote, local, channel);
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
