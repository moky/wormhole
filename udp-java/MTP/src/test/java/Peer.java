
import java.net.SocketAddress;

import chat.dim.mtp.task.Arrival;
import chat.dim.udp.Connection;
import chat.dim.udp.ConnectionStatus;
import chat.dim.udp.HubFilter;
import chat.dim.udp.HubListener;

public class Peer extends chat.dim.mtp.Peer implements HubListener {

    @Override
    public HubFilter getFilter() {
        return null;
    }

    @Override
    public byte[] onDataReceived(byte[] data, SocketAddress source, SocketAddress destination) {
        Arrival task = new Arrival(data, source, destination);
        getPool().appendArrival(task);
        return null;
    }

    @Override
    public void onStatusChanged(Connection connection, ConnectionStatus oldStatus, ConnectionStatus newStatus) {

    }
}
